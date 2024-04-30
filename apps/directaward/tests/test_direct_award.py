import json
from mainsite.tests import BadgrTestCase

from directaward.models import DirectAward, DirectAwardBundle
from issuer.models import BadgeInstance
from lti_edu.models import StudentsEnrolled


class DirectAwardTest(BadgrTestCase):
    def test_create_direct_award_bundle(self):
        teacher1 = self.setup_teacher(
            authenticate=True,
        )
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        post_data = {
            "badgeclass": badgeclass.entity_id,
            "batch_mode": True,
            "notify_recipients": True,
            "direct_awards": [
                {"recipient_email": "some@email.com", "eppn": "some_eppn"},
                {"recipient_email": "some@email2.com", "eppn": "some_eppn2"},
            ],
        }
        response = self.client.post(
            "/directaward/create",
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_direct_award_bundle_failure_atomicity(self):
        teacher1 = self.setup_teacher(
            authenticate=True,
        )
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_direct_award(badgeclass=badgeclass, eppn="duplicate_eppn")
        post_data = {
            "badgeclass": badgeclass.entity_id,
            "direct_awards": [
                {"recipient_email": "some@email.com", "eppn": "unique_eppn"},
                {"recipient_email": "some@email2.com", "eppn": "duplicate_eppn"},
            ],
        }
        response = self.client.post(
            "/directaward/create",
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            DirectAward.objects.filter(eppn="unique_eppn").exists()
        )  # if atomic, this one was not created

    def test_accept_direct_award_from_bundle(self):
        institution = self.setup_institution(identifier="some_home")
        teacher1 = self.setup_teacher(authenticate=True, institution=institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        post_data = {
            "badgeclass": badgeclass.entity_id,
            "batch_mode": True,
            "notify_recipients": True,
            "direct_awards": [
                {"recipient_email": "some@email.com", "eppn": "some_eppn"},
                {"recipient_email": "some@email2.com", "eppn": "some_eppn2"},
            ],
        }
        response = self.client.post(
            "/directaward/create",
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        student = self.setup_student(
            authenticate=True, affiliated_institutions=[teacher1.institution]
        )
        student.add_affiliations([{"eppn": "some_eppn", "schac_home": "some_home"}])
        enrollment = self.enroll_user(
            student, badgeclass
        )  # add enrollment, this one should be removed after accepting direct award
        direct_award_bundle = DirectAwardBundle.objects.get(
            entity_id=response.data["entity_id"]
        )
        response = self.client.post(
            "/directaward/accept/{}".format(
                direct_award_bundle.directaward_set.all()[0].entity_id
            ),
            json.dumps({"accept": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)  # terms not accepted
        terms = badgeclass._get_terms()
        accept_terms_body = [{"terms_entity_id": terms.entity_id, "accepted": True}]
        self.client.post(
            "/user/terms/accept",
            json.dumps(accept_terms_body),
            content_type="application/json",
        )

        response = self.client.post(
            "/directaward/accept/{}".format(
                direct_award_bundle.directaward_set.all()[0].entity_id
            ),
            json.dumps({"accept": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            BadgeInstance.objects.get(
                entity_id=response.data["entity_id"]
            ).direct_award_bundle,
            direct_award_bundle,
        )
        # test that enrollment was removed
        self.assertFalse(StudentsEnrolled.objects.filter(pk=enrollment.pk).exists())

    def test_accept_direct_award_failures(self):
        institution = self.setup_institution(identifier="right_home")
        teacher1 = self.setup_teacher(authenticate=False, institution=institution)
        outside_teacher = self.setup_teacher(authenticate=False)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        student = self.setup_student(
            authenticate=True, affiliated_institutions=[teacher1.institution]
        )
        student.add_affiliations([{"eppn": "wrong_eppn", "schac_home": "right_home"}])
        # eppn mismatch
        direct_award = self.setup_direct_award(badgeclass, eppn="right_eppn")
        response = self.client.post(
            "/directaward/accept/{}".format(direct_award.entity_id),
            json.dumps({"accept": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        outside_student = self.setup_student(
            authenticate=True, affiliated_institutions=[outside_teacher.institution]
        )
        outside_student.add_affiliations(
            [{"eppn": "right_eppn", "schac_home": "wrong_home"}]
        )
        response = self.client.post(
            "/directaward/accept/{}".format(direct_award.entity_id),
            json.dumps({"accept": True}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_and_revoke_direct_award(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        direct_award = self.setup_direct_award(
            created_by=teacher1, badgeclass=badgeclass
        )
        post_data = {"recipient_email": "other@email.com"}
        response = self.client.put(
            "/directaward/edit/{}".format(direct_award.entity_id),
            json.dumps(post_data),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            direct_award.__class__.objects.get(pk=direct_award.pk).recipient_email,
            "other@email.com",
        )
        response = self.client.post(
            "/directaward/revoke-direct-awards",
            json.dumps(
                {
                    "revocation_reason": "revocation_reason",
                    "direct_awards": [{"entity_id": direct_award.entity_id}],
                }
            ),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)


class DirectAwardSchemaTest(BadgrTestCase):
    def test_direct_award_bundle_resolvers(self):
        institution = self.setup_institution()
        teacher1 = self.setup_teacher(authenticate=True, institution=institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        direct_award_bundle = self.setup_direct_award_bundle(badgeclass=badgeclass)
        direct_awards = [
            self.setup_direct_award(badgeclass=badgeclass, bundle=direct_award_bundle)
            for i in range(4)
        ]
        self.setup_assertion(
            recipient=self.setup_student(),
            created_by=teacher1,
            badgeclass=badgeclass,
            direct_award_bundle=direct_award_bundle,
        )
        query = "query foo {badgeClasses {entityId directAwards {entityId} directAwardBundles {entityId initialTotal assertionCount directAwardCount directAwards {entityId} }}}"
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response["data"]["badgeClasses"][0]["directAwardBundles"]))
        self.assertTrue(
            bool(
                response["data"]["badgeClasses"][0]["directAwardBundles"][0][
                    "assertionCount"
                ]
            )
        )
        self.assertTrue(
            bool(
                response["data"]["badgeClasses"][0]["directAwardBundles"][0][
                    "directAwardCount"
                ]
            )
        )
        self.assertTrue(
            bool(
                response["data"]["badgeClasses"][0]["directAwardBundles"][0][
                    "initialTotal"
                ]
            )
        )
