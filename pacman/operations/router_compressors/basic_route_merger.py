from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables
from pacman.exceptions import PacmanRoutingException

from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry

_SPINNAKER_ROUTER_SIZE = 1024


class BasicRouteMerger(object):
    """ Merges routing tables entries via different masks and an\
        exploration process
    """

    __slots__ = ["_bits", "_mask_width", "_key_mask", "_mask_mask", "_width"]

    def __init__(self, width=32, mask_bits=16):
        assert 0 < mask_bits < width
        self._width = width
        self._bits = (1 << width) - 1
        self._mask_width = mask_bits
        self._mask_mask = (1 << mask_bits) - 1
        self._key_mask = self._bits ^ self._mask_mask

    def __call__(self, router_tables):
        tables = MulticastRoutingTables()
        previous_masks = dict()

        progress = ProgressBar(router_tables.routing_tables,
                               "Compressing Routing Tables")

        # Create all masks without holes
        allowed_masks = [self._bits - ((2 ** i) - 1)
                         for i in range(self._width + 1)]

        # Check that none of the masks have "holes" e.g. 0xFFFF0FFF has a hole
        for router_table in router_tables.routing_tables:
            for entry in router_table.multicast_routing_entries:
                if entry.mask not in allowed_masks:
                    raise PacmanRoutingException(
                        "Only masks without holes are allowed in tables for"
                        " BasicRouteMerger (disallowed mask={})".format(
                            hex(entry.mask)))

        for router_table in progress.over(router_tables.routing_tables):
            new_table = self._merge_routes(router_table, previous_masks)
            tables.add_routing_table(new_table)
            n_entries = len([
                entry for entry in new_table.multicast_routing_entries
                if not entry.defaultable])
            # print("Reduced from {} to {}".format(
            #     len(router_table.multicast_routing_entries), n_entries))
            if n_entries >= _SPINNAKER_ROUTER_SIZE:
                raise PacmanRoutingException(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))

        return tables

    def _get_merge_masks(self, mask, previous_masks):
        if mask in previous_masks:
            return previous_masks[mask]

        last_one = self._width + 1 - bin(mask).rfind('1')
        n_bits = self._mask_width - last_one
        merge_masks = sorted(
            [self._mask_mask - ((2 ** n) - 1)
             for n in range(n_bits - 1, self._mask_width + 1)],
            key=lambda x: bin(x).count("1"))

        # print(hex(mask), [hex(m) for m in merge_masks])
        previous_masks[mask] = merge_masks
        return merge_masks

    def _merge_routes(self, router_table, previous_masks):
        merged_routes = MulticastRoutingTable(router_table.x, router_table.y)
        keys_merged = set()

        entries = router_table.multicast_routing_entries
        for router_entry in entries:
            if router_entry.routing_entry_key in keys_merged:
                continue

            mask = router_entry.mask
            if not self._merge_a_route(
                    entries, mask, previous_masks, router_entry,
                    merged_routes, keys_merged):
                merged_routes.add_multicast_routing_entry(router_entry)
                keys_merged.add(router_entry.routing_entry_key)
        return merged_routes

    def _merge_a_route(self, entries, mask, previous_masks, router_entry,
                       routes, keys_merged):
        if mask & self._key_mask != self._key_mask:
            return False
        for extra_bits in self._get_merge_masks(mask, previous_masks):
            new_mask = self._key_mask | extra_bits
            new_key = router_entry.routing_entry_key & new_mask
            new_last_key = self._last_key(new_key, new_mask)

            potential_merges = self._mergeable_entries(
                router_entry, entries, new_key, new_mask, new_last_key,
                keys_merged)
            if len(potential_merges) > 1:
                # if masked_key in routes:
                #     raise Exception("Attempting to merge an existing key")
                routes.add_multicast_routing_entry(MulticastRoutingEntry(
                    new_key, new_mask, router_entry.processor_ids,
                    router_entry.link_ids, defaultable=False))
                keys_merged.update(
                    route.routing_entry_key for route in potential_merges)
                return True
        return False

    def _last_key(self, key, mask):
        n_keys = ~mask & self._bits
        return key + n_keys

    def _mergeable_entries(
            self, entry, entries, new_key, new_mask, new_last_key, merged):
        """ Check that all the cores on this chip have the same route as this\
            is the only way we can merge here.
        """
        potential_merges = set()
        for entry_2 in entries:
            key = entry_2.routing_entry_key
            n_keys = ~entry_2.mask & self._bits
            last_key = key + n_keys
            masked_key = entry_2.routing_entry_key & new_mask
            overlap = (min(new_last_key, last_key) - max(new_key, key)) > 0
            in_range = new_key <= key and new_last_key >= last_key

            if (new_key == masked_key and (
                    not in_range
                    or entry_2.routing_entry_key in merged
                    or entry.processor_ids != entry_2.processor_ids
                    or entry.link_ids != entry_2.link_ids)):
                # Mismatched routes; cannot merge
                return []
            elif new_key == masked_key:
                # This one is mergeable
                potential_merges.add(entry_2)
            elif overlap:
                # Overlapping routes; cannot merge
                return []
        return potential_merges
