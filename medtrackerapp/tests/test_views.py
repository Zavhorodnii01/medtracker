from rest_framework.test import APITestCase
from medtrackerapp.models import Medication, DoseLog
from django.urls import reverse
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch


class MedicationViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(name="Aspirin", dosage_mg=100, prescribed_per_day=2)

    def test_list_medications_valid_data(self):
        """Test retrieving list of all medications (positive path)."""
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")
        self.assertEqual(response.data[0]["dosage_mg"], 100)

    def test_list_medications_empty(self):
        """Test retrieving medications when database is empty (boundary condition)."""
        Medication.objects.all().delete()
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_medication_valid_data(self):
        """Test creating a new medication with valid data (positive path)."""
        url = reverse("medication-list")
        data = {
            "name": "Ibuprofen",
            "dosage_mg": 200,
            "prescribed_per_day": 3
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 2)
        self.assertEqual(response.data["name"], "Ibuprofen")

    def test_create_medication_missing_fields(self):
        """Test creating medication with missing required fields (negative path)."""
        url = reverse("medication-list")
        data = {"name": "Incomplete"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("dosage_mg", response.data)
        self.assertIn("prescribed_per_day", response.data)

    def test_create_medication_invalid_data_types(self):
        """Test creating medication with invalid data types (negative path)."""
        url = reverse("medication-list")
        data = {
            "name": "TestMed",
            "dosage_mg": "invalid",
            "prescribed_per_day": 2
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_medication_valid_id(self):
        """Test retrieving a specific medication by valid ID (positive path)."""
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_retrieve_medication_invalid_id(self):
        """Test retrieving medication with non-existent ID (negative path)."""
        url = reverse("medication-detail", args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_medication_valid_data(self):
        """Test updating medication with valid data (positive path)."""
        url = reverse("medication-detail", args=[self.med.id])
        data = {
            "name": "Aspirin Updated",
            "dosage_mg": 150,
            "prescribed_per_day": 3
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.med.refresh_from_db()
        self.assertEqual(self.med.name, "Aspirin Updated")
        self.assertEqual(self.med.dosage_mg, 150)

    def test_partial_update_medication(self):
        """Test partially updating medication (PATCH) (positive path)."""
        url = reverse("medication-detail", args=[self.med.id])
        data = {"dosage_mg": 125}
        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.med.refresh_from_db()
        self.assertEqual(self.med.dosage_mg, 125)
        self.assertEqual(self.med.name, "Aspirin")

    def test_delete_medication_valid_id(self):
        """Test deleting medication with valid ID (positive path)."""
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Medication.objects.count(), 0)

    def test_delete_medication_invalid_id(self):
        """Test deleting medication with non-existent ID (negative path)."""
        url = reverse("medication-detail", args=[99999])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('medtrackerapp.services.DrugInfoService.get_drug_info')
    def test_get_external_info_success(self, mock_get_drug_info):
        """Test fetching external drug info with successful API response (mocked)."""
        mock_response = {
            "name": "Aspirin",
            "manufacturer": "Bayer",
            "warnings": ["Keep out of reach of children"],
            "purpose": ["Pain reliever"]
        }
        mock_get_drug_info.return_value = mock_response

        url = reverse("medication-get-external-info", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")
        self.assertEqual(response.data["manufacturer"], "Bayer")
        mock_get_drug_info.assert_called_once_with("Aspirin")

    @patch('medtrackerapp.services.DrugInfoService.get_drug_info')
    def test_get_external_info_api_error(self, mock_get_drug_info):
        """Test fetching external drug info when API returns error (mocked)."""
        mock_get_drug_info.side_effect = ValueError("OpenFDA API error: 404")

        url = reverse("medication-get-external-info", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertIn("error", response.data)
        mock_get_drug_info.assert_called_once_with("Aspirin")


class DoseLogViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(name="Metformin", dosage_mg=500, prescribed_per_day=2)
        self.log = DoseLog.objects.create(
            medication=self.med,
            taken_at=timezone.now(),
            was_taken=True
        )

    def test_list_dose_logs_valid_data(self):
        """Test retrieving list of all dose logs (positive path)."""
        url = reverse("doselog-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["medication"], self.med.id)

    def test_list_dose_logs_empty(self):
        """Test retrieving dose logs when database is empty (boundary condition)."""
        DoseLog.objects.all().delete()
        url = reverse("doselog-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_dose_log_valid_data(self):
        """Test creating a new dose log with valid data (positive path)."""
        url = reverse("doselog-list")
        data = {
            "medication": self.med.id,
            "taken_at": timezone.now().isoformat(),
            "was_taken": False
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 2)

    def test_create_dose_log_missing_medication(self):
        """Test creating dose log without medication (negative path)."""
        url = reverse("doselog-list")
        data = {
            "taken_at": timezone.now().isoformat(),
            "was_taken": True
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("medication", response.data)

    def test_create_dose_log_invalid_medication_id(self):
        """Test creating dose log with non-existent medication ID (negative path)."""
        url = reverse("doselog-list")
        data = {
            "medication": 99999,
            "taken_at": timezone.now().isoformat(),
            "was_taken": True
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_dose_log_valid_id(self):
        """Test retrieving a specific dose log by valid ID (positive path)."""
        url = reverse("doselog-detail", args=[self.log.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["was_taken"], True)

    def test_retrieve_dose_log_invalid_id(self):
        """Test retrieving dose log with non-existent ID (negative path)."""
        url = reverse("doselog-detail", args=[99999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_dose_log_valid_data(self):
        """Test updating dose log with valid data (positive path)."""
        url = reverse("doselog-detail", args=[self.log.id])
        new_time = timezone.now() + timedelta(hours=1)
        data = {
            "medication": self.med.id,
            "taken_at": new_time.isoformat(),
            "was_taken": False
        }
        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.log.refresh_from_db()
        self.assertFalse(self.log.was_taken)

    def test_delete_dose_log_valid_id(self):
        """Test deleting dose log with valid ID (positive path)."""
        url = reverse("doselog-detail", args=[self.log.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DoseLog.objects.count(), 0)

    def test_filter_by_date_valid_params(self):
        """Test filtering dose logs by valid date range (positive path)."""
        base_date = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)

        DoseLog.objects.create(medication=self.med, taken_at=base_date - timedelta(days=5), was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=base_date - timedelta(days=3), was_taken=True)
        DoseLog.objects.create(medication=self.med, taken_at=base_date - timedelta(days=1), was_taken=False)

        url = reverse("doselog-filter-by-date")
        start = (base_date - timedelta(days=3)).date().isoformat()
        end = base_date.date().isoformat()
        response = self.client.get(url, {"start": start, "end": end})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_filter_by_date_missing_start_param(self):
        """Test filtering dose logs without start parameter (negative path)."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"end": "2025-11-20"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_filter_by_date_missing_end_param(self):
        """Test filtering dose logs without end parameter (negative path)."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "2025-11-15"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_filter_by_date_invalid_date_format(self):
        """Test filtering dose logs with invalid date format (negative path)."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "invalid-date", "end": "2025-11-20"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_filter_by_date_no_results(self):
        """Test filtering dose logs when no logs match date range (boundary condition)."""
        url = reverse("doselog-filter-by-date")
        response = self.client.get(url, {"start": "2020-01-01", "end": "2020-01-31"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
