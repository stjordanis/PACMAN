from pacman.model.routing_tables \
    import MulticastRoutingTable, MulticastRoutingTables
from pacman.exceptions import PacmanRoutingException

from spinn_utilities.progress_bar import ProgressBar
from spinn_machine import MulticastRoutingEntry

_MASK = 0xFFFF0000L
_LOW_32_BITS = 0xFFFFFFFFL


class BasicRouteMerger(object):
    """ functionality to merge routing tables entries via different masks and
    a exploration process

    """

    __slots__ = []

    def __call__(self, router_tables):
        tables = MulticastRoutingTables()
        previous_masks = dict()

        progress = ProgressBar(router_tables.routing_tables,
                               "Compressing Routing Tables")

        # Create all masks without holes
        allowed_masks = [_LOW_32_BITS - ((2 ** i) - 1) for i in range(33)]

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
            print "Reduced from {} to {}".format(
                len(router_table.multicast_routing_entries), n_entries)
            if n_entries > 1023:
                raise PacmanRoutingException(
                    "Cannot make table small enough: {} entries".format(
                        n_entries))

        return tables

    def _get_merge_masks(self, mask, previous_masks):
        if mask in previous_masks:
            return previous_masks[mask]

        last_one = 33 - bin(mask).rfind('1')
        n_bits = 16 - last_one
        merge_masks = sorted(
            [0xFFFF - ((2 ** n) - 1) for n in range(n_bits - 1, 17)],
            key=lambda x: bin(x).count("1"))

        # print hex(mask), [hex(m) for m in merge_masks]
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
            if mask & _MASK != _MASK or not self._merge_a_route(
                    entries, mask, previous_masks, router_entry,
                    merged_routes, keys_merged):
                merged_routes.add_multicast_routing_entry(router_entry)
                keys_merged.add(router_entry.routing_entry_key)
        return merged_routes

    def _merge_a_route(self, entries, mask, previous_masks, router_entry,
                       routes, keys_merged):
        for extra_bits in self._get_merge_masks(mask, previous_masks):
            new_mask = _MASK | extra_bits
            new_key = router_entry.routing_entry_key & new_mask
            new_last_key = self._last_key(new_key, new_mask)

            # Check that all the cores on this chip have the same route
            # as this is the only way we can merge here
            mergable = True
            potential_merges = set()
            for entry_2 in entries:
                key = entry_2.routing_entry_key
                last_key = self._last_key(key, entry_2.mask)
                masked_key = entry_2.routing_entry_key & new_mask
                in_range = new_key <= key and new_last_key >= last_key
                if new_key == masked_key and (
                        not in_range
                        or entry_2.routing_entry_key in keys_merged
                        or router_entry.processor_ids != entry_2.processor_ids
                        or router_entry.link_ids != entry_2.link_ids):
                    mergable = False
                    break
                elif new_key == masked_key:
                    potential_merges.add(entry_2)
                elif min(new_last_key, last_key) - max(new_key, key) > 0:
                    mergable = False
                    break

            if mergable and potential_merges:
                # if masked_key in routes:
                #     raise Exception("Attempting to merge an existing key")
                routes.add_multicast_routing_entry(MulticastRoutingEntry(
                    new_key, new_mask, router_entry.processor_ids,
                    router_entry.link_ids, defaultable=False))
                keys_merged.update(
                    route.routing_entry_key for route in potential_merges)
                return True
        return False

    @staticmethod
    def _last_key(key, mask):
        n_keys = ~mask & _LOW_32_BITS
        return key + n_keys
