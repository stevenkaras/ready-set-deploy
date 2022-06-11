from ready_set_deploy.components import Component


class Gatherer:
    def empty(self) -> Component:
        """
        Returns an empty component in the shape of this provider (that is, with empty elements with the correct names and types)
        """
        raise NotImplementedError("empty")

    def gather_local(self, *, qualifier: tuple[str, ...] = ()) -> Component:
        raise NotImplementedError("gather_local")
