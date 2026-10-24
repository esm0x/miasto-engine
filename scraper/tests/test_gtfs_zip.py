"""Which files of a city's GTFS zip are taken, on the shapes cities actually ship."""

import io
import unittest
import zipfile

from sources.transit.gtfs_link import REQUIRED, gtfs_members

FEED = REQUIRED + ["calendar.txt", "calendar_dates.txt", "feed_info.txt", "shapes.txt"]


def zip_of(names):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in names:
            if n.endswith("/"):
                z.writestr(zipfile.ZipInfo(n), b"")
            else:
                z.writestr(n, f"content of {n}".encode())
    return zipfile.ZipFile(io.BytesIO(buf.getvalue())).infolist()


class Members(unittest.TestCase):

    def test_plain_root_feed(self):
        self.assertEqual(set(FEED), set(gtfs_members(zip_of(FEED))))

    def test_km_rybnik_october_2026_folder_and_mac_junk(self):
        """Attachment 643, exactly as published: GTFS-KMR/ plus __MACOSX resource forks."""
        names = (["GTFS-KMR/"] + [f"GTFS-KMR/{n}" for n in FEED]
                 + ["__MACOSX/._GTFS-KMR"] + [f"__MACOSX/GTFS-KMR/._{n}" for n in FEED])
        got = gtfs_members(zip_of(names))
        self.assertEqual(set(FEED), set(got))
        self.assertEqual("GTFS-KMR/stops.txt", got["stops.txt"].filename)

    def test_root_wins_over_a_folder(self):
        got = gtfs_members(zip_of(FEED + [f"extra/{n}" for n in FEED]))
        self.assertEqual("stops.txt", got["stops.txt"].filename)

    def test_two_folders_are_refused(self):
        with self.assertRaises(RuntimeError):
            gtfs_members(zip_of([f"a/{n}" for n in FEED] + [f"b/{n}" for n in FEED]))

    def test_a_name_twice_is_refused(self):
        """A second stops.txt later in the zip is how a checked file gets swapped."""
        with self.assertRaises(RuntimeError):
            gtfs_members(zip_of(FEED + ["stops.txt"]))


if __name__ == "__main__":
    unittest.main()
