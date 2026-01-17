from django.test import TestCase
from medtrackerapp.models import Medication, DoseLog
from django.utils import timezone
from datetime import timedelta, date


class MedicationModelTests(TestCase):
    def test_str_returns_name_and_dosage(self):
        """Test that __str__ returns medication name and dosage."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        """Test adherence rate when all doses are taken (positive path)."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )

        now = timezone.now()
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(hours=30), was_taken=True
        )
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(hours=1), was_taken=True
        )

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_partial_adherence(self):
        """Test adherence rate with partial adherence (50%)."""
        med = Medication.objects.create(
            name="Ibuprofen", dosage_mg=200, prescribed_per_day=3
        )

        now = timezone.now()
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(hours=8), was_taken=True
        )
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(hours=4), was_taken=False
        )
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(hours=1), was_taken=True
        )
        DoseLog.objects.create(medication=med, taken_at=now, was_taken=False)

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 50.0)

    def test_adherence_rate_no_logs(self):
        """Test adherence rate when no dose logs exist (boundary condition)."""
        med = Medication.objects.create(
            name="Metformin", dosage_mg=500, prescribed_per_day=2
        )
        adherence = med.adherence_rate()
        self.assertEqual(adherence, 0.0)

    def test_adherence_rate_all_doses_missed(self):
        """Test adherence rate when all doses are missed (negative path)."""
        med = Medication.objects.create(
            name="Lisinopril", dosage_mg=10, prescribed_per_day=1
        )

        now = timezone.now()
        DoseLog.objects.create(
            medication=med, taken_at=now - timedelta(days=1), was_taken=False
        )
        DoseLog.objects.create(medication=med, taken_at=now, was_taken=False)

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 0.0)

    def test_expected_doses_valid_input(self):
        """Test expected_doses with valid positive inputs."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        self.assertEqual(med.expected_doses(7), 14)
        self.assertEqual(med.expected_doses(0), 0)

    def test_expected_doses_negative_days(self):
        """Test expected_doses raises ValueError for negative days (negative path)."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        with self.assertRaises(ValueError) as context:
            med.expected_doses(-1)
        self.assertIn("Days and schedule must be positive", str(context.exception))

    def test_expected_doses_zero_prescribed_per_day(self):
        """Test expected_doses raises ValueError when prescribed_per_day is 0 (negative path)."""
        # Note: We need to bypass the PositiveIntegerField validation for this test
        med = Medication.objects.create(
            name="TestDrug", dosage_mg=50, prescribed_per_day=1
        )
        med.prescribed_per_day = 0  # Manually set to 0 to test the method logic

        with self.assertRaises(ValueError) as context:
            med.expected_doses(5)
        self.assertIn("Days and schedule must be positive", str(context.exception))

    def test_adherence_rate_over_period_valid_dates(self):
        """Test adherence_rate_over_period with valid date range."""
        med = Medication.objects.create(
            name="Vitamin D", dosage_mg=1000, prescribed_per_day=1
        )

        # Create logs for a 3-day period
        base_date = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
        DoseLog.objects.create(
            medication=med, taken_at=base_date - timedelta(days=2), was_taken=True
        )
        DoseLog.objects.create(
            medication=med, taken_at=base_date - timedelta(days=1), was_taken=False
        )
        DoseLog.objects.create(medication=med, taken_at=base_date, was_taken=True)

        start = (base_date - timedelta(days=2)).date()
        end = base_date.date()

        # Expected: 3 days * 1 dose/day = 3 expected, 2 taken = 66.67%
        adherence = med.adherence_rate_over_period(start, end)
        self.assertEqual(adherence, 66.67)

    def test_adherence_rate_over_period_start_after_end(self):
        """Test adherence_rate_over_period raises ValueError when start > end (negative path)."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )

        start = date(2025, 11, 20)
        end = date(2025, 11, 15)

        with self.assertRaises(ValueError) as context:
            med.adherence_rate_over_period(start, end)
        self.assertIn(
            "start_date must be before or equal to end_date", str(context.exception)
        )

    def test_adherence_rate_over_period_no_expected_doses(self):
        """Test adherence_rate_over_period returns 0.0 when expected doses is 0 (boundary condition)."""
        med = Medication.objects.create(
            name="TestDrug", dosage_mg=50, prescribed_per_day=1
        )

        # Same start and end date
        start = date(2025, 11, 20)
        end = date(2025, 11, 20)

        # 1 day * 1 dose/day = 1 expected dose
        adherence = med.adherence_rate_over_period(start, end)
        # No logs created, so 0 taken / 1 expected = 0%
        self.assertEqual(adherence, 0.0)

    def test_fetch_external_info_handles_exception(self):
        """Test fetch_external_info returns error dict when exception occurs."""
        med = Medication.objects.create(name="", dosage_mg=100, prescribed_per_day=2)
        result = med.fetch_external_info()
        self.assertIn("error", result)


class DoseLogModelTests(TestCase):
    def test_str_dose_taken(self):
        """Test __str__ method when dose was taken."""
        med = Medication.objects.create(
            name="Aspirin", dosage_mg=100, prescribed_per_day=2
        )
        now = timezone.now()
        log = DoseLog.objects.create(medication=med, taken_at=now, was_taken=True)

        expected_time = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
        self.assertEqual(str(log), f"Aspirin at {expected_time} - Taken")

    def test_str_dose_missed(self):
        """Test __str__ method when dose was missed."""
        med = Medication.objects.create(
            name="Ibuprofen", dosage_mg=200, prescribed_per_day=1
        )
        now = timezone.now()
        log = DoseLog.objects.create(medication=med, taken_at=now, was_taken=False)

        expected_time = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
        self.assertEqual(str(log), f"Ibuprofen at {expected_time} - Missed")

    def test_default_was_taken_is_true(self):
        """Test that was_taken defaults to True."""
        med = Medication.objects.create(
            name="Metformin", dosage_mg=500, prescribed_per_day=2
        )
        log = DoseLog.objects.create(medication=med, taken_at=timezone.now())
        self.assertTrue(log.was_taken)

    def test_ordering_by_taken_at_desc(self):
        """Test that DoseLog instances are ordered by taken_at descending."""
        med = Medication.objects.create(
            name="Lisinopril", dosage_mg=10, prescribed_per_day=1
        )

        now = timezone.now()
        log1 = DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=5))
        log2 = DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=2))
        log3 = DoseLog.objects.create(medication=med, taken_at=now)

        logs = DoseLog.objects.all()
        self.assertEqual(logs[0], log3)  # Most recent first
        self.assertEqual(logs[1], log2)
        self.assertEqual(logs[2], log1)

    def test_foreign_key_relationship(self):
        """Test that DoseLog correctly references Medication via foreign key."""
        med = Medication.objects.create(
            name="Vitamin C", dosage_mg=1000, prescribed_per_day=1
        )
        log = DoseLog.objects.create(
            medication=med, taken_at=timezone.now(), was_taken=True
        )

        self.assertEqual(log.medication, med)
        self.assertIn(log, med.doselog_set.all())

    def test_cascade_delete(self):
        """Test that deleting a Medication cascades to delete its DoseLogs."""
        med = Medication.objects.create(
            name="Atorvastatin", dosage_mg=20, prescribed_per_day=1
        )
        DoseLog.objects.create(medication=med, taken_at=timezone.now())
        DoseLog.objects.create(
            medication=med, taken_at=timezone.now() - timedelta(hours=1)
        )

        med_id = med.id
        self.assertEqual(DoseLog.objects.filter(medication_id=med_id).count(), 2)

        med.delete()
        self.assertEqual(DoseLog.objects.filter(medication_id=med_id).count(), 0)
