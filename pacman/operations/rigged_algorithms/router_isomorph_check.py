class RouterIsomorphChecker(object):

    def __call__(self, report_folder, routing_tables, routing_tables_copy):
        if self.check(routing_tables, routing_tables_copy):
            print "The two sets are routes are the same."
        else:
            print "The routes are different."

    def check(self, routing_tables, routing_tables_copy):
        """

        MulticastRoutingTableByPartition
        format: entry, router_x, router_y, partition
        dict mapping (x,y)-> dict mapping (partition)-> routing table entry
        entry format: out_going_links, outgoing_processors,
        incoming_processor=None, incoming_link=None"""


        for table in routing_tables:
