import hashlib
import os
import shutil

from django.conf import settings
from django.core import management
from django.test import TestCase
from django.test.client import Client

from server.models import Data, Case, Processor, GenUser, iterate_schema
from server.tasks import manager
from ..utils import create_test_case, clear_all


class BaseProcessorTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        clear_all()

        super(BaseProcessorTestCase, cls).setUpClass()

        cls.user = GenUser.objects.create_superuser(email="admin@genialis.com")
        management.call_command('register')

    def setUp(self):
        super(BaseProcessorTestCase, self).setUp()

        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.case = create_test_case(self.user.pk)['c1']

    def tearDown(self):
        super(BaseProcessorTestCase, self).tearDown()

        # Delete Data objects and their files
        for d in Data.objects.all():
            data_dir = os.path.join(settings.DATAFS['data_path'], str(d.pk))
            shutil.rmtree(data_dir, ignore_errors=True)
            d.delete()

    def get_field(self, obj, path):
        for p in path.split('.'):
            obj = obj[p]
        return obj

    def run_processor(self, processor_name, input_):
        p = Processor.objects.get(name=processor_name)

        for field_schema, fields in iterate_schema(input_, p['input_schema']):
            # copy referenced files to upload dir
            if field_schema['type'] == "basic:file:":
                old_path = os.path.join(self.current_path, 'inputs', fields[field_schema['name']])
                shutil.copy2(old_path, settings.FILE_UPLOAD_TEMP_DIR)
                file_name = os.path.basename(fields[field_schema['name']])
                fields[field_schema['name']] = {
                    'file': file_name,
                    'file_temp': file_name,
                    'is_remote': False,
                }

            # convert primary keys to strings
            if field_schema['type'].startswith('data:'):
                fields[field_schema['name']] = str(fields[field_schema['name']])
            if field_schema['type'].startswith('list:data:'):
                for obj in fields[field_schema['name']]:
                    obj = str(obj)

            # fill field with default values if empty
            if 'default' in field_schema and field_schema['name'] not in fields:
                fields[field_schema['name']] = field_schema['default']

        d = Data(
            input=input_,
            author_id=self.user.pk,
            processor_name=processor_name,
            case_ids=[self.case.pk],
        )
        d.save()
        manager(run_sync=True)

        return Data.objects.get(pk=d.pk)

    def assertFields(self, obj, path, value):
        field = self.get_field(obj['output'], path)
        self.assertEqual(field, str(value))

    def assertFiles(self, obj, field_path, fn):
        field = self.get_field(obj['output'], field_path)
        output = os.path.join(settings.DATAFS['data_path'], str(obj.pk), field['file'])
        output_hash = hashlib.sha256(open(output).read()).hexdigest()

        wanted = os.path.join(self.current_path, 'outputs', fn)
        wanted_hash = hashlib.sha256(open(wanted).read()).hexdigest()

        return wanted_hash == output_hash