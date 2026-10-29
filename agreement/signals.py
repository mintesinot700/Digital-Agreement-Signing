"""
Signals for the agreement app:
- Audit trail: every agreement create/update/status-change/delete is recorded.
- Email notifications: submission confirmation to the signer and status-change
  notifications to the signer (uses the configured Django email backend).
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from .models import Agreement, AuditLog

logger = logging.getLogger(__name__)

STATUS_MESSAGES = {
    'approved': 'Good news! Your agreement "{type}" has been APPROVED.',
    'rejected': 'Your agreement "{type}" has been rejected. Please contact support for details.',
    'pending': 'Your agreement "{type}" is pending review.',
}


def _send_status_email(agreement):
    recipient = (agreement.email_account or '').strip()
    if not recipient or '@' not in recipient:
        return  # no valid email on the agreement — skip silently
    message = STATUS_MESSAGES.get(
        agreement.status,
        'The status of your agreement "{type}" has changed.'
    ).format(type=agreement.pdf_agreement_name or 'agreement')

    try:
        send_mail(
            subject=f'Agreement {agreement.status.title()} — Digital Agreement Signing',
            message=(
                f'Hello {agreement.your_name},\n\n'
                f'{message}\n\n'
                f'Submitted on: {agreement.submited_date:%Y-%m-%d %H:%M}\n'
                f'Current status: {agreement.status.title()}\n\n'
                f'— Digital Agreement Signing Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception as exc:  # never break the request flow because of SMTP issues
        logger.warning('Failed to send status email for agreement #%s: %s', agreement.pk, exc)


def log_action(agreement, action, details='', actor=None):
    try:
        AuditLog.objects.create(
            agreement_id=agreement.pk if agreement else None,
            agreement_name=f"{agreement.your_name}'s Agreement" if agreement else '',
            agreement_type=agreement.pdf_agreement_name or '' if agreement else '',
            action=action,
            actor=actor if getattr(actor, 'is_authenticated', False) else None,
            actor_name=getattr(actor, 'username', '') or 'anonymous',
            details=details,
        )
    except Exception as exc:
        logger.warning('Failed to write audit log: %s', exc)


@receiver(post_save, sender=Agreement, dispatch_uid='agreement_audit_and_notify')
def agreement_post_save(sender, instance, created, **kwargs):
    if created:
        log_action(
            instance,
            'created',
            details=f'Agreement "{instance.pdf_agreement_name}" submitted by {instance.your_name}.',
        )
        _send_submission_confirmation(instance)
    else:
        # _original_status is snapshotted when the instance is loaded/created
        old_status = getattr(instance, '_original_status', instance.status)
        if old_status != instance.status:
            log_action(
                instance,
                'status_changed',
                details=f'Status changed from "{old_status}" to "{instance.status}".',
            )
            _send_status_email(instance)
        else:
            log_action(instance, 'updated', details='Agreement details updated.')


@receiver(post_delete, sender=Agreement, dispatch_uid='agreement_audit_delete')
def agreement_post_delete(sender, instance, **kwargs):
    log_action(
        instance,
        'deleted',
        details=f'Agreement "{instance.pdf_agreement_name}" for {instance.your_name} was deleted.',
    )


def _send_submission_confirmation(agreement):
    recipient = (agreement.email_account or '').strip()
    if not recipient or '@' not in recipient:
        return
    try:
        send_mail(
            subject='Agreement received — Digital Agreement Signing',
            message=(
                f'Hello {agreement.your_name},\n\n'
                f'Your agreement "{agreement.pdf_agreement_name}" was received on '
                f'{agreement.submited_date:%Y-%m-%d %H:%M} and is now pending review.\n\n'
                f'You will receive another email once it is approved or rejected.\n\n'
                f'— Digital Agreement Signing Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=True,
        )
    except Exception as exc:
        logger.warning('Failed to send confirmation email for agreement #%s: %s', agreement.pk, exc)
