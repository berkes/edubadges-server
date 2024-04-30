import logging

from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db import connections
from django.utils import timezone


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        from directaward.models import DirectAwardBundle, DirectAward

        # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
        connections.close_all()

        logger = logging.getLogger("Badgr.Debug")
        logger.info("Running award_scheduled_direct_awards")

        direct_award_bundles = DirectAwardBundle.objects.filter(
            scheduled_at__lt=timezone.now(), status=DirectAwardBundle.STATUS_SCHEDULED
        ).all()

        for bundle in direct_award_bundles:
            for da in bundle.directaward_set.all():
                da.status = DirectAward.STATUS_UNACCEPTED
                da.badgeclass.remove_cached_data(["cached_direct_awards"])
                da.badgeclass.remove_cached_data(["cached_direct_award_bundles"])
                try:
                    da.save()
                    da.notify_recipient()
                except IntegrityError:
                    pass

            bundle.status = DirectAwardBundle.STATUS_ACTIVE
            bundle.scheduled_at = None
            bundle.save()
            bundle.notify_awarder()

            bundle.remove_cached_data(["cached_direct_awards"])

        logger.info(
            f"Finished {len(direct_award_bundles)} award_scheduled_direct_awards"
        )
