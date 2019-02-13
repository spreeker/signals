from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from signals.apps.signals import permissions, workflow
from signals.apps.signals.models import Priority
from tests.apps.signals.attachment_helpers import small_gif
from tests.apps.signals.factories import (
    CategoryAssignmentFactory,
    SignalFactory,
    SubCategoryFactory
)
from tests.apps.users.factories import UserFactory


class TestCategoryPermissions(APITestCase):
    """
    This class tests the category permissions. A user can only see/edit signals he has access to.
    Category permission checks will be skipped for users that have the SIA_BACKOFFICE permission.


    endpoint                            sia_backoffice   limited access

    v0
    all auth endpoints                     full access   no access

    v1
    GET /signals/v1/private/signals        full access   only signals in assigned categories
    GET /signals/v1/private/signals/{id}   full access   only signals from assigned categories
    PATCH /signals/v1/private/signals/{id} full access   only signals from assigned categories
    PATCH /signals/v1/private/signals/{id} full access   do not move signal to not-assigned category
    """

    signals = []
    categories = []
    assigned_categories = []
    assigned_signals = []
    user = None

    class PermissionTest:
        user = None
        all_signals_ids = None
        all_categories_ids = None
        test_class = None

        # Default everything closed
        v0_access = False
        signals_access_ids = []
        signals_no_access_ids = []
        categories_access_ids = []
        categories_no_access_ids = []

        location = {
            "geometrie": {
                "type": "Point",
                "coordinates": [
                    4.898466,
                    52.361585
                ]
            },
            "stadsdeel": "A",
            "buurt_code": "aaa1",
            "address": {},
            "extra_properties": {}
        }

        def __init__(self, user, signals, categories, test_class):
            self.user = user
            self.all_signals_ids = [signal.id for signal in signals]
            self.all_categories_ids = [category.id for category in categories]
            self.test_class = test_class

        def should_have_v0_access(self, v0_access: bool = True):
            self.v0_access = v0_access

        def should_have_access_to_signals(self, signals: list):
            self.signals_access_ids = [signal.id for signal in signals]
            self.signals_no_access_ids = self._list_difference(self.all_signals_ids,
                                                               self.signals_access_ids)

        def should_have_access_to_categories(self, categories: list):
            self.categories_access_ids = [category.id for category in categories]
            self.categories_no_access_ids = self._list_difference(self.all_categories_ids,
                                                                  self.categories_access_ids)

        def execute(self):
            self.test_class.client.force_authenticate(user=self.user)

            self._test_v0_access()
            self._test_v1_get_signals()
            self._test_v1_get_signal_by_id()
            self._test_v1_update_signals_in_category()
            self._test_v1_update_signals_move_to_other_category()

        def _list_difference(self, left: list, right: list):
            return [item for item in left if item not in right]

        def _test_get_endpoint(self, endpoint: str, expected_status_code: int):
            response = self.test_class.client.get(endpoint)
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _test_post_endpoint(self, endpoint: str, data: dict, expected_status_code: int):
            response = self.test_class.client.post(endpoint, data, format='json')
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _test_patch_endpoint(self, endpoint: str, data: dict, expected_status_code: int):
            response = self.test_class.client.patch(endpoint, data)
            self.test_class.assertEquals(expected_status_code, response.status_code)
            return response

        def _get_ids_from_response_list(self, result: list):
            return [item['id'] for item in result]

        def _test_v0_access(self):
            # Expected status codes
            post_status_code = 201 if self.v0_access else 403
            get_status_code = 200 if self.v0_access else 403

            # Test that user has access to all v0 endpoints, or to none

            response = self._test_get_endpoint('/signals/auth/signal/', get_status_code)

            if get_status_code == 200:
                # Check response
                self.test_class.assertEquals(len(self.all_signals_ids),
                                             len(response.json()['results']))

            for signal_id in self.all_signals_ids:
                self._test_get_endpoint('/signals/auth/signal/{}/'.format(signal_id),
                                        get_status_code)

            for signal_id in self.all_signals_ids:
                status = {
                    '_signal': signal_id,
                    'state': workflow.AFWACHTING,
                }

                self._test_post_endpoint('/signals/auth/status/', status, post_status_code)

                location = self.location
                location['_signal'] = signal_id

                self._test_post_endpoint('/signals/auth/location/', location, post_status_code)

                category = {
                    '_signal': signal_id,
                    'main': 'Overlast op het water',
                    'sub': 'Overlast op het water - snel varen',
                }

                self._test_post_endpoint('/signals/auth/category/', category, post_status_code)

                note = {
                    '_signal': signal_id,
                    'text': 'Test note',
                }

                self._test_post_endpoint('/signals/auth/note/', note, post_status_code)

                priority = {
                    '_signal': signal_id,
                    'priority': Priority.PRIORITY_HIGH,
                }

                self._test_post_endpoint('/signals/auth/priority/', priority, post_status_code)

        def _test_v1_get_signals(self):
            """ Test that GET /signals/v1/private/signals/ response only contains signals we have
            access to """

            response = self._test_get_endpoint('/signals/v1/private/signals/', 200)
            ids = self._get_ids_from_response_list(response.json()['results'])

            # Test correct id's in response.
            self.test_class.assertEquals(len(self.signals_access_ids), len(ids))
            self.test_class.assertEquals(set(self.signals_access_ids), set(ids))

            # Should never fail, but knowing that the length of the list and sets are equal (ie we
            # don't have doubles), means we can get away with not checking if the signals we don't
            # have access to aren't showing up in the response.
            self.test_class.assertEquals(len(ids), len(set(ids)))

        def _test_v1_get_signal_by_id(self):
            """ Test that GET /signals/v1/private/signals/{id}/ only gives us access to the signals
            we have access to """

            endpoint = '/signals/v1/private/signals/{}'

            for signal_id in self.signals_access_ids:
                self._test_get_endpoint(endpoint.format(signal_id), 200)

            for signal_id in self.signals_no_access_ids:
                self._test_get_endpoint(endpoint.format(signal_id), 403)

        def _test_v1_add_attachment_to_signals(self):
            """ Test that POST /signals/v1/private/signals/{id}/attachments/ only allows us to post
            a new attachment to signals we have access to """

            endpoint = '/signals/v1/private/signals/{}/attachments/'

            for signal_id in self.signals_access_ids:
                image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
                self._test_post_endpoint(endpoint.format(signal_id), {'file': image}, 201)

            for signal_id in self.signals_no_access_ids:
                image = SimpleUploadedFile('image.gif', small_gif, content_type='image/gif')
                self._test_post_endpoint(endpoint.format(signal_id), {'file': image}, 403)

        def _test_v1_update_signals_in_category(self):
            # Test we can only update signals in our own categories
            pass

        def _test_v1_update_signals_move_to_other_category(self):
            # Test we can only move signals between own categories
            pass

    def setUp(self):
        """
        Method creates a number of categories and signals. Part of the categories and signals will
        be added to the 'assigned' lists. These lists should be used to assign permissions to the
        user.

        :return:
        """
        self.signals = []
        self.assigned_signals = []
        self.categories = [SubCategoryFactory.create() for _ in range(5)]
        self.assigned_categories = []

        for idx, category in enumerate(self.categories):
            assign = idx % 2 == 0

            if assign:
                self.assigned_categories.append(category)

            for _ in range(5):
                signal = SignalFactory.create()
                category_assignment = CategoryAssignmentFactory(_signal=signal,
                                                                sub_category=category)
                signal.category_assignment = category_assignment
                signal.save()
                self.signals.append(signal)

                if assign:
                    self.assigned_signals.append(signal)

    def _user_add_default_permissions(self, user: User):
        # V0 permissions
        user.user_permissions.add(Permission.objects.get(codename='add_note'))
        user.user_permissions.add(Permission.objects.get(codename='add_priority'))
        user.user_permissions.add(Permission.objects.get(codename='add_location'))
        user.user_permissions.add(Permission.objects.get(codename='add_categoryassignment'))
        user.user_permissions.add(Permission.objects.get(codename='add_status'))

        # V1 permissions
        user.user_permissions.add(Permission.objects.get(codename=permissions.SIA_READ))
        user.user_permissions.add(Permission.objects.get(codename=permissions.SIA_WRITE))

    def test_sia_no_permissions(self):
        """ User without backoffice permissions should not have v0 access """
        no_backoffice_permissions_user = UserFactory.create()
        self._user_add_default_permissions(no_backoffice_permissions_user)

        test = self.__class__.PermissionTest(no_backoffice_permissions_user, self.signals,
                                             self.categories, self)
        test.should_have_access_to_categories([])
        test.should_have_access_to_signals([])
        test.should_have_v0_access(False)

        test.execute()

    def test_sia_backoffice_permission(self):
        """ User with backoffice permissions should have full v0 access. """
        backoffice_permission = Permission.objects.get(codename=permissions.SIA_BACKOFFICE)
        backoffice_user = UserFactory.create()
        backoffice_user.user_permissions.add(backoffice_permission)
        self._user_add_default_permissions(backoffice_user)

        test = self.__class__.PermissionTest(backoffice_user, self.signals, self.categories, self)
        test.should_have_access_to_categories(self.categories)
        test.should_have_access_to_signals(self.signals)
        test.should_have_v0_access()

        test.execute()

    def test_permission_test_class_list_difference(self):
        """ Test the test class. Quis custodiet ipsos custodes? """

        class IdObject:
            def __init__(self, id):
                self.id = id

        permission_test = self.__class__.PermissionTest(UserFactory.create(),
                                                        [IdObject(1), IdObject(2), IdObject(3),
                                                         IdObject(4), IdObject(5)],
                                                        [IdObject(6), IdObject(7), IdObject(8),
                                                         IdObject(9), IdObject(10)],
                                                        self)

        permission_test.should_have_access_to_signals([IdObject(1), IdObject(2), IdObject(3)])
        self.assertEquals([4, 5], permission_test.signals_no_access_ids)

        permission_test.should_have_access_to_categories([IdObject(7), IdObject(8), IdObject(9)])
        self.assertEquals([6, 10], permission_test.categories_no_access_ids)