"""
API tests for the agreement app: submission, ownership-scoped listings,
admin review with status filter, summary-PDF generation, audit trail and
email notifications.
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from django.test import TestCase
from PIL import Image
from reportlab.pdfgen import canvas as pdf_canvas

from rest_framework.test import APIClient

from Accounts.models import UserAccounts
from .models import Agreement, AuditLog, Pdf_agreement

AGREEMENT_URL = '/api/agreement/'
MY_AGREEMENTS_URL = '/api/my-agreements/'
AGREEMENT_LIST_URL = '/api/agreement_list/'
AUDIT_LOG_URL = '/api/audit-log/'

PNG_1X1 = None
SMALL_PDF = None


def make_png():
    """A small valid PNG produced with PIL (passes the image validator)."""
    global PNG_1X1
    if PNG_1X1 is None:
        buffer = io.BytesIO()
        Image.new('RGB', (4, 4), color=(46, 204, 113)).save(buffer, format='PNG')
        PNG_1X1 = buffer.getvalue()
    return PNG_1X1


def make_pdf():
    """A tiny valid PDF produced with ReportLab (passes the PDF validator)."""
    global SMALL_PDF
    if SMALL_PDF is None:
        buffer = io.BytesIO()
        page = pdf_canvas.Canvas(buffer)
        page.drawString(100, 750, 'Test agreement template')
        page.save()
        SMALL_PDF = buffer.getvalue()
    return SMALL_PDF


def image_file(name='photo.png'):
    return SimpleUploadedFile(name, make_png(), content_type='image/png')


def pdf_file(name='template.pdf'):
    return SimpleUploadedFile(name, make_pdf(), content_type='application/pdf')


def base_agreement_payload(pdf_agreement_id, **overrides):
    payload = {
        'pdf_agreement': pdf_agreement_id,
        'your_name': 'John Doe',
        'father_name': 'Michael Doe',
        'grand_father_name': 'Robert Doe',
        'gender': 'M',
        'address': 'Bole Road #12',
        'city': 'Addis Ababa',
        'nationality': 'Ethiopian',
        'phone_number': '+251911234567',
        'email_account': 'john@example.com',
        'profile_photo': image_file('profile.png'),
        'photo_of_userID': image_file('userid.png'),
        'signature': image_file('signature.png'),
    }
    payload.update(overrides)
    return payload


class AgreementTestBase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserAccounts.objects.create_user(
            username='signer', email='signer@example.com',
            password='StrongPass!123', phone_number='+251911234567',
        )
        self.other_user = UserAccounts.objects.create_user(
            username='other', email='other@example.com',
            password='StrongPass!123', phone_number='+251911234568',
        )
        self.staff = UserAccounts.objects.create_user(
            username='reviewer', email='reviewer@example.com',
            password='StrongPass!123', phone_number='+251911234569',
            is_staff=True,
        )
        self.template = Pdf_agreement.objects.create(
            type_of_agreement='Rental Agreement',
            pdf_file=pdf_file('rental.pdf'),
        )


class AgreementCreateAPITest(AgreementTestBase):
    def test_submit_agreement_success(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            AGREEMENT_URL, base_agreement_payload(self.template.id), format='multipart'
        )
        self.assertEqual(response.status_code, 201)
        agreement = Agreement.objects.get(pk=response.data['id'])
        self.assertEqual(agreement.user, self.user)
        self.assertEqual(agreement.status, 'pending')
        self.assertEqual(agreement.pdf_agreement_name, 'Rental Agreement')

    def test_submission_writes_audit_log_and_sends_confirmation_email(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            AGREEMENT_URL, base_agreement_payload(self.template.id), format='multipart'
        )
        self.assertTrue(
            AuditLog.objects.filter(action='created', agreement_name__icontains='John').exists()
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('john@example.com', mail.outbox[0].to)

    def test_missing_signature_rejected(self):
        self.client.force_authenticate(user=self.user)
        payload = base_agreement_payload(self.template.id)
        payload.pop('signature')
        response = self.client.post(AGREEMENT_URL, payload, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_invalid_name_rejected(self):
        self.client.force_authenticate(user=self.user)
        payload = base_agreement_payload(self.template.id, your_name='J0hn 123')
        response = self.client.post(AGREEMENT_URL, payload, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_authentication_required(self):
        response = self.client.post(
            AGREEMENT_URL, base_agreement_payload(self.template.id), format='multipart'
        )
        self.assertEqual(response.status_code, 401)


class MyAgreementsAPITest(AgreementTestBase):
    def test_returns_only_own_agreements(self):
        Agreement.objects.create(
            user=self.user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name='John Doe',
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234567',
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )
        Agreement.objects.create(
            user=self.other_user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name='Other Person',
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234568',
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MY_AGREEMENTS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['your_name'], 'John Doe')

    def test_requires_authentication(self):
        response = self.client.get(MY_AGREEMENTS_URL)
        self.assertEqual(response.status_code, 401)


class AgreementListAdminAPITest(AgreementTestBase):
    def _create(self, user, name, status='pending'):
        return Agreement.objects.create(
            user=user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name=name,
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234567', status=status,
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )

    def test_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(AGREEMENT_LIST_URL)
        self.assertEqual(response.status_code, 403)

    def test_admin_sees_all_with_status_filter(self):
        self._create(self.user, 'Alpha Person', status='pending')
        self._create(self.other_user, 'Beta Person', status='approved')
        self.client.force_authenticate(user=self.staff)

        all_response = self.client.get(AGREEMENT_LIST_URL)
        self.assertEqual(all_response.status_code, 200)
        self.assertEqual(len(all_response.data), 2)

        pending_response = self.client.get(AGREEMENT_LIST_URL, {'status': 'pending'})
        self.assertEqual(len(pending_response.data), 1)
        self.assertEqual(pending_response.data[0]['status'], 'pending')

    def test_admin_search_by_name(self):
        self._create(self.user, 'Alpha Person')
        self._create(self.other_user, 'Beta Person')
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(AGREEMENT_LIST_URL, {'search': 'beta'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['your_name'], 'Beta Person')


class AgreementReviewAPITest(AgreementTestBase):
    def setUp(self):
        super().setUp()
        self.agreement = Agreement.objects.create(
            user=self.user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name='John Doe',
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234567',
            email_account='john@example.com',
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )
        # Creating the agreement triggers the "received" confirmation email;
        # clear the outbox so status-change tests assert on their own email.
        mail.outbox.clear()

    def test_admin_can_change_status_and_email_is_sent(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            f'/api/agreement/{self.agreement.id}/', {'status': 'approved'}, format='json'
        )
        self.assertEqual(response.status_code, 200)
        self.agreement.refresh_from_db()
        self.assertEqual(self.agreement.status, 'approved')

        # Status-change email + audit entry
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('approved', mail.outbox[0].subject.lower())
        self.assertTrue(
            AuditLog.objects.filter(
                action='status_changed', agreement_id=self.agreement.id
            ).exists()
        )

    def test_regular_user_cannot_review(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            f'/api/agreement/{self.agreement.id}/', {'status': 'approved'}, format='json'
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_agreement_and_audit_log_records_it(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.delete(f'/api/agreement/{self.agreement.id}/')
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Agreement.objects.filter(pk=self.agreement.id).exists())
        self.assertTrue(
            AuditLog.objects.filter(action='deleted', agreement_id=self.agreement.id).exists()
        )

    def test_detail_404_for_unknown_id(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get('/api/agreement/999999/')
        self.assertEqual(response.status_code, 404)


class AgreementPDFDownloadAPITest(AgreementTestBase):
    def setUp(self):
        super().setUp()
        self.agreement = Agreement.objects.create(
            user=self.user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name='John Doe',
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234567',
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )

    def test_owner_can_download_summary_pdf(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f'/api/agreement/{self.agreement.id}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        content = b''.join(response.streaming_content)
        self.assertTrue(content.startswith(b'%PDF'))
        # PDF generation is recorded in the audit trail
        self.assertTrue(
            AuditLog.objects.filter(
                action='pdf_generated', agreement_id=self.agreement.id
            ).exists()
        )

    def test_other_user_forbidden(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.get(f'/api/agreement/{self.agreement.id}/pdf/')
        self.assertEqual(response.status_code, 403)

    def test_admin_allowed(self):
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(f'/api/agreement/{self.agreement.id}/pdf/')
        self.assertEqual(response.status_code, 200)

    def test_anonymous_unauthorized(self):
        response = self.client.get(f'/api/agreement/{self.agreement.id}/pdf/')
        self.assertEqual(response.status_code, 401)


class AuditLogAPITest(AgreementTestBase):
    def test_forbidden_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, 403)

    def test_admin_can_read_audit_trail(self):
        Agreement.objects.create(
            user=self.user, pdf_agreement=self.template,
            pdf_agreement_name='Rental Agreement', your_name='John Doe',
            father_name='a', grand_father_name='a', address='x', city='Addis Ababa',
            nationality='Ethiopian', phone_number='+251911234567',
            profile_photo=image_file(), photo_of_userID=image_file(),
            signature=image_file(),
        )
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(entry['action'] == 'created' for entry in response.data))


class PdfTemplateAPITest(AgreementTestBase):
    def test_admin_can_create_template(self):
        self.client.force_authenticate(user=self.staff)
        payload = {'type_of_agreement': 'Employment Contract', 'pdf_file': pdf_file('emp.pdf')}
        response = self.client.post('/api/pdf_agreement/create/', payload, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Pdf_agreement.objects.filter(type_of_agreement='Employment Contract').exists())

    def test_non_pdf_upload_rejected(self):
        self.client.force_authenticate(user=self.staff)
        payload = {
            'type_of_agreement': 'Employment Contract',
            'pdf_file': SimpleUploadedFile('fake.pdf', make_png(), content_type='image/png'),
        }
        response = self.client.post('/api/pdf_agreement/create/', payload, format='multipart')
        self.assertEqual(response.status_code, 400)

    def test_template_list_is_public(self):
        response = self.client.get('/api/pdf_agreement/')
        self.assertEqual(response.status_code, 200)

    def test_regular_user_cannot_create_template(self):
        self.client.force_authenticate(user=self.user)
        payload = {'type_of_agreement': 'Employment Contract', 'pdf_file': pdf_file('emp.pdf')}
        response = self.client.post('/api/pdf_agreement/create/', payload, format='multipart')
        self.assertEqual(response.status_code, 403)


class PdfFileServeAPITest(AgreementTestBase):
    def test_serves_bundled_sample_when_no_file_attached(self):
        template = Pdf_agreement.objects.create(type_of_agreement='Rental Agreement (UI Demo)')
        response = self.client.get(f'/api/pdf/{template.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('sample_rental_agreement.pdf', response['Content-Disposition'])
        self.assertIn(b'%PDF', b''.join(response.streaming_content))

    def test_serves_uploaded_template_file(self):
        response = self.client.get(f'/api/pdf/{self.template.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertNotIn('sample_rental_agreement.pdf', response.get('Content-Disposition', ''))
        self.assertIn(b'%PDF', b''.join(response.streaming_content))

    def test_unknown_template_404(self):
        response = self.client.get('/api/pdf/99999/')
        self.assertEqual(response.status_code, 404)
