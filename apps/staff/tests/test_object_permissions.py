import json
import collections
from mainsite.tests import BadgrTestCase


class ObjectPermissionTests(BadgrTestCase):
    def test_may_not_escalate_your_own_perms(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        staff = self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=False
        )
        data = json.dumps(
            {
                "may_create": 0,
                "may_read": 1,
                "may_update": 0,
                "may_delete": 0,
                "may_sign": 0,
                "may_award": 0,
                "may_administrate_users": 1,
            }
        )
        response = self.client.put(
            "/staff-membership/faculty/change/{}".format(staff.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.delete(
            "/staff-membership/institution/change/{}".format(staff.entity_id),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_may_not_administrate_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=False
        )
        data = json.dumps(
            {
                "may_create": 0,
                "may_read": 1,
                "may_update": 0,
                "may_delete": 0,
                "may_sign": 0,
                "may_award": 0,
                "may_administrate_users": 0,
                "user": teacher2.entity_id,
                "faculty": faculty.entity_id,
            }
        )
        response = self.client.post(
            "/staff-membership/faculty/{}/create".format(faculty.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(404, response.status_code)

    def test_may_not_assign_perms_you_dont_have(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=True
        )
        data = json.dumps(
            {
                "may_create": 1,
                "may_read": 1,
                "may_update": 1,
                "may_delete": 1,
                "may_sign": 1,
                "may_award": 1,
                "may_administrate_users": 0,
                "user": teacher2.entity_id,
                "faculty": faculty.entity_id,
            }
        )
        response = self.client.post(
            "/staff-membership/faculty/{}/create".format(faculty.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(
            str(response.data[0]),
            "May not assign permissions that you don't have yourself",
        )

    def test_create_all_staffs(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        teacher3 = self.setup_teacher(institution=teacher1.institution)
        teacher4 = self.setup_teacher(institution=teacher1.institution)
        teacher5 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=True
        )
        data = {
            "may_create": 0,
            "may_read": 1,
            "may_update": 0,
            "may_delete": 0,
            "may_sign": 0,
            "may_award": 0,
            "may_administrate_users": 1,
            "user": teacher2.entity_id,
            "badgeclass": badgeclass.entity_id,
        }
        response = self.client.post(
            "/staff-membership/badgeclass/{}/create".format(badgeclass.entity_id),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data["user"] = teacher3.entity_id
        data["issuer"] = issuer.entity_id
        del data["badgeclass"]
        response = self.client.post(
            "/staff-membership/issuer/{}/create".format(issuer.entity_id),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data["user"] = teacher4.entity_id
        data["faculty"] = faculty.entity_id
        del data["issuer"]
        response = self.client.post(
            "/staff-membership/faculty/{}/create".format(faculty.entity_id),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data["user"] = teacher5.entity_id
        data["institution"] = teacher1.institution.entity_id
        del data["faculty"]
        response = self.client.post(
            "/staff-membership/institution/{}/create".format(
                teacher1.institution.entity_id
            ),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_update_faculty_staff_membership(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, faculty, may_read=True, may_administrate_users=True
        )
        staff = self.setup_staff_membership(
            teacher2, faculty, may_read=True, may_administrate_users=False
        )
        self.assertEqual(len(teacher2.cached_faculty_staffs()), 1)
        data = json.dumps(
            {
                "may_create": 0,
                "may_read": 1,
                "may_update": 0,
                "may_delete": 0,
                "may_sign": 0,
                "may_award": 0,
                "may_administrate_users": 1,
            }
        )
        response = self.client.put(
            "/staff-membership/faculty/change/{}".format(staff.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            teacher2.cached_faculty_staffs()[0].permissions, json.loads(data)
        )  # perms updated instantly

    def test_update_institution_staff_membership(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=True
        )
        staff_to_edit = self.setup_staff_membership(
            teacher2, teacher1.institution, may_read=True, may_administrate_users=True
        )
        data = json.dumps(
            {
                "may_create": 0,
                "may_read": 0,
                "may_update": 0,
                "may_delete": 0,
                "may_sign": 0,
                "may_award": 0,
                "may_administrate_users": 0,
            }
        )
        response = self.client.put(
            "/staff-membership/institution/change/{}".format(staff_to_edit.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            teacher2.cached_institution_staff().permissions, json.loads(data)
        )  # perms updated instantly

    def test_may_not_create_staff_membership_for_user_outside_institution(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher()
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=True
        )
        data = {
            "may_create": 0,
            "may_read": 1,
            "may_update": 0,
            "may_delete": 0,
            "may_sign": 0,
            "may_award": 0,
            "may_administrate_users": 0,
            "faculty": faculty.entity_id,
            "user": teacher2.entity_id,
        }
        response = self.client.post(
            "/staff-membership/faculty/{}/create".format(faculty.entity_id),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_may_not_change_staff_membership_outside_administrable_scope(self):
        """user is in scope, but staff membership is not"""
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty1 = self.setup_faculty(institution=teacher1.institution)
        faculty2 = self.setup_faculty(institution=teacher1.institution)
        issuer1 = self.setup_issuer(faculty=faculty1, created_by=teacher1)
        self.setup_staff_membership(
            teacher1, faculty1, may_read=True, may_administrate_users=True
        )
        self.setup_staff_membership(
            teacher2, issuer1, may_read=True, may_administrate_users=True
        )
        staff = self.setup_staff_membership(
            teacher2, faculty2, may_read=True, may_administrate_users=True
        )
        data = {
            "may_create": 0,
            "may_read": 1,
            "may_update": 0,
            "may_delete": 0,
            "may_sign": 0,
            "may_award": 0,
            "may_administrate_users": 0,
        }
        response = self.client.put(
            "/staff-membership/faculty/change/{}".format(staff.entity_id),
            json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_permission_tree_cleanup_after_change(self):
        # create entities outside branch
        outside_teacher = self.setup_teacher()
        outside_faculty = self.setup_faculty(institution=outside_teacher.institution)
        outside_issuer = self.setup_issuer(
            faculty=outside_faculty, created_by=outside_teacher
        )
        outside_badgeclass = self.setup_badgeclass(issuer=outside_issuer)
        # create entities inside  branch
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer0 = self.setup_issuer(faculty=faculty, created_by=teacher1)
        issuer1 = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer1)
        badgeclass1 = self.setup_badgeclass(issuer=issuer1)
        # test branch returns
        branchfrom_issuer1_viewpoint = [
            teacher1.institution,
            issuer1,
            faculty,
            badgeclass,
            badgeclass1,
        ]
        branch = issuer1.get_all_entities_in_branch()
        # returned branch and expected branch are similar
        self.assertEqual(
            collections.Counter(branch),
            collections.Counter(branchfrom_issuer1_viewpoint),
        )
        # test staff member duplicates in branch throws exception
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_update=True, may_administrate_users=True
        )
        self.setup_staff_membership(teacher2, teacher2.institution, may_read=True)
        data = json.dumps(
            {
                "may_create": 0,
                "may_read": 0,
                "may_update": 1,
                "may_delete": 0,
                "may_sign": 0,
                "may_award": 0,
                "may_administrate_users": 0,
                "user": teacher2.entity_id,
                "issuer": issuer1.entity_id,
            }
        )
        response = self.client.post(
            "/staff-membership/issuer/{}/create".format(issuer1.entity_id),
            data,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data[0].__str__(),
            "Cannot save staff membership, there is a conflicting staff membership.",
        )

    def test_student_may_not_access_fields_through_graphql(self):
        """certain fields are blocked for students"""
        pass

    def test_student_may_query_entity_lists_through_graphql(self):
        """queries like all institutions / faculties should result in empty values"""
        pass

    def test_delete_staff_membership(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty1 = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_read=True, may_administrate_users=True
        )
        staff = self.setup_staff_membership(
            teacher2, faculty1, may_read=True, may_administrate_users=True
        )
        response = self.client.delete(
            "/staff-membership/faculty/change/{}".format(staff.entity_id),
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 204)
        self.assertEqual(faculty1.staff_items.__len__(), 0)

    def test_may_not_remove_last_institution_staff_membership(self):
        teacher1 = self.setup_teacher(authenticate=True)
        staff = self.setup_staff_membership(
            teacher1, teacher1.institution, may_administrate_users=True
        )
        response = self.client.delete(
            "/staff-membership/institution/change/{}".format(staff.entity_id),
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 400)
        self.assertEqual(
            response.data["fields"]["error_message"].__str__(),
            "Cannot remove the last staff membership of this institution.",
        )

    def test_cannot_delete_institution_staff_membership(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_administrate_users=True
        )
        staff = self.setup_staff_membership(
            teacher2, teacher1.institution, may_administrate_users=True
        )
        response = self.client.delete(
            "/staff-membership/faculty/change/{}".format(staff.entity_id),
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 404)

    def test_all_teachers_in_institution_may_read(self):
        teacher1 = self.setup_teacher(authenticate=True)
        outside_teacher = self.setup_teacher()
        student = self.setup_student()
        faculty = self.setup_faculty(institution=teacher1.institution)
        query = 'query foo {faculty(id: "' + faculty.entity_id + '") {entityId}}'
        response_ok = self.graphene_post(teacher1, query)
        self.assertEqual(response_ok["data"]["faculty"]["entityId"], faculty.entity_id)
        response_empty = self.graphene_post(outside_teacher, query)
        self.assertEqual(response_empty["data"]["faculty"], None)
        response_empty = self.graphene_post(student, query)
        self.assertEqual(response_empty["data"]["faculty"], None)
