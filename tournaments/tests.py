from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date
import json

from users.models import Coach, Member
from tournaments.models import Tournament


class TournamentModuleTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user_coach = User.objects.create_user(username="coach1", password="test123")
        self.user_member = User.objects.create_user(username="member1", password="test123")
        self.user_other = User.objects.create_user(username="other", password="test123")

        self.coach = Coach.objects.create(
            user=self.user_coach,
            city="Jakarta",
            phone="08123456789",
            description="Experienced coach",
            sport="football",
            hourly_fee=250000
        )

        self.member = Member.objects.create(
            user=self.user_member,
            city="Depok",
            phone="08987654321",
            description="Active member"
        )

        self.tournament = Tournament.objects.create(
            pembuatTournaments=self.coach,
            tipeTournaments="football",
            namaTournaments="Liga UI",
            tanggalTournaments=date.today(),
            lokasiTournaments="Lapangan UI",
            deskripsiTournaments="Turnamen antar fakultas",
            posterTournaments="https://example.com/poster.png",
            flagTournaments=True
        )

    def test_tournament_view_html(self):
        response = self.client.get(reverse("tournaments:tournament_view"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tournament_list.html")
        self.assertIn("tournaments", response.context)

    def test_tournament_view_ajax(self):
        response = self.client.get(
            reverse("tournaments:tournament_view"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tournaments", data)
        self.assertEqual(data["tournaments"][0]["nama"], "Liga UI")

    def test_my_tournaments_ajax_as_coach(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.get(
            reverse("tournaments:my_tournaments_ajax"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("tournaments", response.json())

    def test_my_tournaments_ajax_as_member(self):
        self.client.login(username="member1", password="test123")
        self.tournament.pesertaTournaments.add(self.member)
        response = self.client.get(
            reverse("tournaments:my_tournaments_ajax"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["tournaments"]), 1)

    def test_my_tournaments_invalid_request(self):
        self.client.login(username="member1", password="test123")
        response = self.client.get(reverse("tournaments:my_tournaments_ajax"))
        self.assertEqual(response.status_code, 400)

    def test_tournament_show_html(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.get(
            reverse("tournaments:tournament_show", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tournament_show.html")
        self.assertIn("tournament", response.context)

    def test_tournament_show_ajax(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.get(
            reverse("tournaments:tournament_show", args=[self.tournament.idTournaments]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("tournament", data)

    def test_create_tournament_as_coach_success(self):
        self.client.login(username="coach1", password="test123")
        data = {
            "namaTournaments": "Turnamen Baru",
            "tipeTournaments": "futsal",
            "tanggalTournaments": date.today(),
            "lokasiTournaments": "Depok",
            "deskripsiTournaments": "Deskripsi baru",
            "posterTournaments": "https://poster2.png",
        }
        response = self.client.post(reverse("tournaments:create_tournament"), data=data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tournament.objects.filter(namaTournaments="Turnamen Baru").exists())

    def test_delete_tournament_as_coach(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.post(
            reverse("tournaments:delete_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Tournament.objects.filter(idTournaments=self.tournament.idTournaments).exists())

    def test_delete_tournament_ajax(self):
        self.client.login(username="coach1", password="test123")
        t2 = Tournament.objects.create(
            pembuatTournaments=self.coach,
            tipeTournaments="futsal",
            namaTournaments="Ajax Tournament",
            tanggalTournaments=date.today(),
            lokasiTournaments="Jakarta",
            deskripsiTournaments="Desc",
            posterTournaments="https://example.com/img.png",
        )
        response = self.client.delete(
            reverse("tournaments:delete_tournament", args=[t2.idTournaments]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"message": "Tournament berhasil dihapus!"})

    def test_delete_tournament_forbidden(self):
        self.client.login(username="other", password="test123")
        response = self.client.post(
            reverse("tournaments:delete_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 403)

    def test_assign_tournament_success(self):
        self.client.login(username="member1", password="test123")
        response = self.client.post(
            reverse("tournaments:assign_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.tournament.pesertaTournaments.filter(pk=self.member.pk).exists())

    def test_assign_tournament_already_registered(self):
        self.client.login(username="member1", password="test123")
        self.tournament.pesertaTournaments.add(self.member)
        response = self.client.post(
            reverse("tournaments:assign_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("Anda sudah terdaftar", response.json()["message"])

    def test_assign_tournament_closed(self):
        self.client.login(username="member1", password="test123")
        self.tournament.flagTournaments = False
        self.tournament.save()
        response = self.client.post(
            reverse("tournaments:assign_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 400)

    def test_assign_tournament_not_member(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.post(
            reverse("tournaments:assign_tournament", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 403)

    def test_edit_tournament_ajax_get(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.get(
            reverse("tournaments:edit_tournament_ajax", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("namaTournaments", response.json())

    def test_edit_tournament_ajax_post(self):
        self.client.login(username="coach1", password="test123")
        payload = {
            "namaTournaments": "Updated Name",
            "lokasiTournaments": "Lapangan Baru",
            "tanggalTournaments": str(date.today()),
            "deskripsiTournaments": "Deskripsi Update",
            "posterTournaments": "https://newposter.png",
        }
        response = self.client.post(
            reverse("tournaments:edit_tournament_ajax", args=[self.tournament.idTournaments]),
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.tournament.refresh_from_db()
        self.assertEqual(self.tournament.namaTournaments, "Updated Name")

    def test_edit_tournament_invalid_method(self):
        self.client.login(username="coach1", password="test123")
        response = self.client.put(
            reverse("tournaments:edit_tournament_ajax", args=[self.tournament.idTournaments])
        )
        self.assertEqual(response.status_code, 405)
