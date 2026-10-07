import json
import math
import time
import uuid

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


HOST = "0.0.0.0"
PORT = 8000

players = {}


def clean_players():
    now = time.time()

    for pid in list(players):
        if now - players[pid]["last"] > 5:
            del players[pid]


class Handler(SimpleHTTPRequestHandler):

    def translate_path(self, path):

        if path == "/" or path == "/index.html":
            return "static/index.html"

        return "static/" + path.lstrip("/")


    def send_json(self, data, code=200):

        raw = json.dumps(data).encode()

        self.send_response(code)
        self.send_header(
            "Content-Type",
            "application/json"
        )
        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )
        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.end_headers()

        self.wfile.write(raw)


    def do_GET(self):

        parsed = urlparse(self.path)

        if parsed.path == "/state":

            query = parse_qs(parsed.query)

            pid = query.get(
                "id",
                [""]
            )[0]

            clean_players()

            snapshot = {
                key: value.copy()
                for key, value in players.items()
            }

            for value in snapshot.values():
                value["last"] = None

            self.send_json({
                "players": snapshot,
                "me": pid
            })

            return

        super().do_GET()


    def do_POST(self):

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        try:

            data = json.loads(
                self.rfile.read(length)
                or b"{}"
            )

        except:

            data = {}


        # OYUNCU KATILMA

        if self.path == "/join":

            pid = uuid.uuid4().hex[:8]

            players[pid] = {

                "x": float(
                    data.get("x", 0)
                ),

                "y": float(
                    data.get("y", 0)
                ),

                "a": 0,

                "hp": 100,

                "name": str(
                    data.get(
                        "name",
                        "Player"
                    )
                )[:16],

                "last": time.time()
            }

            self.send_json({
                "id": pid
            })

            return


        # OYUNCU HAREKETİ

        if self.path == "/update":

            pid = str(
                data.get(
                    "id",
                    ""
                )
            )

            if pid in players:

                p = players[pid]

                p["x"] = float(
                    data.get(
                        "x",
                        p["x"]
                    )
                )

                p["y"] = float(
                    data.get(
                        "y",
                        p["y"]
                    )
                )

                p["a"] = float(
                    data.get(
                        "a",
                        p["a"]
                    )
                )

                p["hp"] = max(
                    0,
                    min(
                        100,
                        int(
                            data.get(
                                "hp",
                                p["hp"]
                            )
                        )
                    )
                )

                p["last"] = time.time()

            self.send_json({
                "ok": True
            })

            return


        # ATEŞ ETME

        if self.path == "/shoot":

            pid = str(
                data.get(
                    "id",
                    ""
                )
            )

            angle = float(
                data.get(
                    "a",
                    0
                )
            )

            shooter = players.get(pid)

            if shooter:

                sx = shooter["x"]
                sy = shooter["y"]

                hit = None
                best_distance = 999

                for oid, target in players.items():

                    if oid == pid:
                        continue

                    if target["hp"] <= 0:
                        continue

                    dx = target["x"] - sx
                    dy = target["y"] - sy

                    distance = math.hypot(
                        dx,
                        dy
                    )

                    if distance > 25:
                        continue

                    target_angle = math.atan2(
                        dy,
                        dx
                    )

                    difference = (
                        target_angle - angle
                    )

                    difference = (
                        difference + math.pi
                    ) % (
                        2 * math.pi
                    ) - math.pi

                    if abs(difference) < 0.10:

                        if distance < best_distance:

                            best_distance = distance
                            hit = oid


                if hit:

                    players[hit]["hp"] -= 25

                    if players[hit]["hp"] <= 0:

                        players[hit]["hp"] = 100

                        players[hit]["x"] = 0
                        players[hit]["y"] = 0

                    self.send_json({
                        "hit": True,
                        "target": hit
                    })

                    return


            self.send_json({
                "hit": False
            })

            return


        self.send_json({
            "error": "Not found"
        }, 404)


    def log_message(self, format, *args):

        print(
            format % args
        )


print("One Shot FPS server başlatılıyor...")
print("http://127.0.0.1:8000")


server = ThreadingHTTPServer(
    (HOST, PORT),
    Handler
)


server.serve_forever()