from ready_set_deploy.model import SubsystemState, SubsystemStateType


class MultiversionPackageManagerMixin:
    PROVIDER_NAME = NotImplemented

    def _elements_to_multiversions(self, elements: list[tuple[str, list[str]]]) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for package, versions in elements:
            result.setdefault(package, set())
            result[package] |= set(versions)

        return result

    def _multiversions_to_elements(self, multiversions: dict[str, set[str]]) -> list[tuple[str, list[str]]]:
        return [(package, list(versions)) for package, versions in sorted(multiversions.items())]

    def _diff_multiversion(self, left: dict[str, set[str]], right: dict[str, set[str]]) -> dict[str, set[str]]:
        result = {}

        for package, versions in left.items():
            for version in versions:
                if version not in right.get(package, set()):
                    result.setdefault(package, set()).add(version)

        return result

    def diff(self, left: SubsystemState, right: SubsystemState) -> tuple[SubsystemState, SubsystemState]:
        # compute the diff that would transform left into right
        assert left.state_type == SubsystemStateType.FULL
        assert right.state_type == SubsystemStateType.FULL
        assert left.qualifier == right.qualifier

        left_packages = self._elements_to_multiversions(left.elements)
        right_packages = self._elements_to_multiversions(right.elements)

        to_add = self._diff_multiversion(right_packages, left_packages)
        to_remove = self._diff_multiversion(left_packages, right_packages)

        desired = SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.DESIRED,
            elements=self._multiversions_to_elements(to_add),
        )
        undesired = SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.UNDESIRED,
            elements=self._multiversions_to_elements(to_remove),
        )

        return desired, undesired

    def _add_multiversion(self, left: dict[str, set[str]], to_add: dict[str, set[str]]) -> dict[str, set[str]]:
        result = {}
        for package, versions in left.items():
            result[package] = set(versions)
        for package, versions in to_add.items():
            result.setdefault(package, set())
            result[package] |= versions

        return result

    def _remove_multiversion(self, left: dict[str, set[str]], to_remove: dict[str, set[str]]) -> dict[str, set[str]]:
        result = {}
        for package, versions in left.items():
            result[package] = set(versions)
        for package, versions in to_remove.items():
            result.setdefault(package, set())
            result[package] -= versions
            if not result[package]:
                result.pop(package, None)

        return result

    def apply_partial_to_full(self, full: SubsystemState, partial: SubsystemState) -> SubsystemState:
        assert full.state_type == SubsystemStateType.FULL
        assert partial.state_type != SubsystemStateType.FULL

        full_packages = self._elements_to_multiversions(full.elements)
        partial_packages = self._elements_to_multiversions(partial.elements)

        if partial.state_type == SubsystemStateType.DESIRED:
            combined = self._add_multiversion(full_packages, partial_packages)
        else:
            combined = self._remove_multiversion(full_packages, partial_packages)

        return SubsystemState(
            name=self.PROVIDER_NAME,
            state_type=SubsystemStateType.FULL,
            elements=self._multiversions_to_elements(combined),
        )
