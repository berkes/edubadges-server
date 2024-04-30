from django.db import models, transaction
from django.db.models import ProtectedError

from staff.models import PermissionedRelationshipBase


class PermissionedModelMixin(object):
    """
    Abstract class used for inheritance by all the Models (Badgeclass, Issuer, Faculty & Institution) that have a related
    Staff model. Used for retrieving permissions and staff members. And instant caching when changes happen.
    """

    def _get_local_permissions(self, user):
        """
        :param user: BadgeUser (teacher)
        :return: a permissions dictionary for the instance only, without looking higher in the hierarchy.
        """
        staff = self.get_staff_member(user)
        if staff:
            return staff.permissions
        else:
            return PermissionedRelationshipBase.empty_permissions()

    def check_local_permissions(self, user, required_permissions):
        """
        This checks if user has all the given permissions on this object
        :param user: BadgeUser (teacher)
        :param required_permissions: a list of strings
        :return: Boolean
        """
        user_permissions = self._get_local_permissions(user)
        if user_permissions:
            perm_count = 0
            for perm in required_permissions:
                if user_permissions[perm]:
                    perm_count += 1
            return perm_count == len(required_permissions)
        return False

    def get_all_staff_memberships_in_current_branch(
        self, user, check_parents=True, check_children=True
    ):
        """
        returns all staff memberships beloning to this user in the branch that this entity is part of
        :param user: BadgeUser
        :param check_parents: bool
        :param check_children: bool
        :return: required_permissions: a list of staff memberships
        """
        all_entities_in_my_branch = self.get_all_entities_in_branch(
            check_parents=check_parents, check_children=check_children
        )
        all_staff_memberships_in_my_branch = []
        for entity in all_entities_in_my_branch:
            all_staff_memberships_in_my_branch += entity.cached_staff()
        return [
            staff for staff in all_staff_memberships_in_my_branch if staff.user == user
        ]

    def get_all_entities_in_branch(self, check_parents=True, check_children=True):
        """
        Recursively walks the tree up and down to get all the entities of the current branch (where self is a node).
        returns self, all the parents and all the children
        """
        entities = [self]
        if check_parents:
            try:
                entities += self.parent.get_all_entities_in_branch(check_children=False)
            except AttributeError:
                if not check_children:
                    return entities
        if check_children:
            try:
                for child in self.children:
                    entities += child.get_all_entities_in_branch(check_parents=False)
            except AttributeError:
                return entities
        return entities

    def get_permissions(self, user):
        """
        This method returns (inherited or local) permissions for the instance by climbing the permission tree.
        :param user: BadgeUser (teacher)
        :return: a permissions dictionary
        """
        try:
            parent_perms = self.parent.get_permissions(user)
            local_perms = self._get_local_permissions(user)
            combined_perms = {}
            for key in local_perms:
                combined_perms[key] = (
                    local_perms[key]
                    if local_perms[key] > parent_perms[key]
                    else parent_perms[key]
                )
            return combined_perms
        except AttributeError:  # recursive base case (reached root of permission tree, i.e. the Institution)
            perms = self._get_local_permissions(user)
            if (
                hasattr(user, "is_teacher")
                and user.is_teacher
                and self == user.institution
            ):  # if at the recursive base case the institution is the same as user's institution
                perms["may_read"] = (
                    True  # then add may_read, everyone in institution is a reader
                )
            return perms

    def has_permissions(self, user, permissions):
        """
        This method checks to see if a user has all the given permissions on an object
        :param user: BadgeUser (teacher)
        :param permissions: a list of strings
        :return: True if user has all the permissions
        """
        user_perms = self.get_permissions(user)
        perm_count = 0
        if not user_perms:
            return False
        else:
            for perm in permissions:
                if not user_perms[perm]:
                    return False
                else:
                    perm_count += 1
            return len(permissions) == perm_count

    @property
    def staff_items(self):
        return self.cached_staff()

    def get_local_staff_members(self, permissions=None):
        """
        gets the staff members belonging to this object that have all of the permissions given
        :param permissions: array of permissions required
        :return: list of staff memberships that have this
        """
        result = []
        if permissions:
            for staff in self.staff_items:
                has_perms = []
                for perm in permissions:
                    if staff.permissions[perm]:
                        has_perms.append(perm)
                if len(has_perms) == len(permissions):
                    result.append(staff)
            return result
        else:
            return self.staff_items

    def get_staff_member(self, user):
        """
        Get a staff membership object belonging to the given user.
        :param user: BadgeUser (teacher)
        :return: Staff object
        """
        for staff in self.staff_items:
            if staff.user == user:
                return staff

    def publish(self, *args, **kwargs):
        super(PermissionedModelMixin, self).publish(*args, **kwargs)
        for member in self.cached_staff():
            member.cached_user.publish()

    def save(self, *args, **kwargs):
        super(PermissionedModelMixin, self).save(*args, **kwargs)
        try:
            self.parent.publish()
        except AttributeError:
            pass

    @transaction.atomic
    def delete(self, *args, **kwargs):
        """
        Recursive delete function that
            - deletes all children
            - only publishes the parent of the initially deleted entity
            - removes all associated staff memberships without publishing the associated object (the one that is deleted)
        """
        publish_parent = kwargs.pop("publish_parent", True)
        if self.assertions:
            raise ProtectedError(
                "{} may only be deleted if there are no awarded Assertions.".format(
                    self.__class__.__name__
                ),
                self,
            )
        try:  # first the children
            kids = self.children
            for child in kids:
                child.delete(publish_parent=False)
        except AttributeError:  # no kids
            pass
        for membership in self.staff_items:
            membership.delete(publish_object=False)
        ret = super(PermissionedModelMixin, self).delete(*args, **kwargs)
        if publish_parent:
            try:
                self.parent.publish()
            except AttributeError:  # no parent
                pass
        return ret

    def return_value_according_to_language(self, attribute_english, attribute_dutch):
        """Convenience function that returns the right attribute according to the
        language selection of its parent institution"""
        if self.__class__.__name__ == "Institution":
            institution = self
        else:
            institution = self.institution
        if institution.default_language == institution.DEFAULT_LANGUAGE_ENGLISH:
            if attribute_english:
                return attribute_english
        elif institution.default_language == institution.DEFAULT_LANGUAGE_DUTCH:
            if attribute_dutch:
                return attribute_dutch
        return attribute_english if attribute_english else attribute_dutch
