import logging

from django.core.management.base import BaseCommand

from signals.apps.signals.models import Signal
from signals.apps.zds import zds_client
from signals.apps.zds.tasks import (
    add_document_to_case,
    connect_signal_to_case,
    create_case,
    create_document
)
from signals.apps.zds.workflow import ZTC_STATUSSES

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate the ZDS components with the old signals that were already in the system."

    def handle(self, *args, **options):
        signals = Signal.objects.filter(case__isnull=True)
        for signal in signals:
            self.local_create_case(signal)

    def local_create_case(self, signal):
        try:
            create_case(signal)
            connect_signal_to_case(signal)
            if signal.image:
                create_document(signal)
                add_document_to_case(signal)

            for status in signal.statuses.order_by('created_at'):
                # This is done custom so we can add all statusses
                data = {
                    'zaak': signal.case.zrc_link,
                    'statusType': ZTC_STATUSSES.get(status.state),
                    'datumStatusGezet': status.created_at.isoformat(),
                }

                zds_client.zrc.create('status', data)
        except Exception as e:
            logger.exception(e)
            self.stderr.write(repr(e))