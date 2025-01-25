from http.server import BaseHTTPRequestHandler, HTTPServer
from dataclasses import dataclass
from enum import Enum
import json
import shutil
import threading
from time import sleep

import qrcode
import utils


BLOWING_TIME = 15
RESULT_SCREEN_TIME = 15
CREDIT_FOR_BLOWING = 100
PUBLIC_SERVER_URL = "https://duvaj.ga"
CURRENT_BLOW_IMAGE_NAME = "current_blow_image.jpg"
CREDIT_STORE_FILE = "credit_store"


class StateName(Enum):
    COMMERICALS = "commercials"
    CAN_BLOW = "can_blow"
    BLOWING = "blowing"
    RESULT = "result"


@dataclass
class State:
    name: StateName
    credit: int
    alcohol: int
    current_max: int
    blowing_time_left: int
    result_screen_time_left: int
    alcohol_result: int
    image_path: str | None
    qr_path: str | None
    videos: list[str]


def load_credit() -> 0:
    try:
        with open(CREDIT_STORE_FILE, "r") as f:
            return int(f.read())
    except FileNotFoundError:
        return 0


state = State(
    name=StateName.COMMERICALS,
    credit=load_credit(),
    alcohol=0,
    current_max=0,
    blowing_time_left=0,
    result_screen_time_left=0,
    image_path=None,
    qr_path=None,
    alcohol_result=0,
    videos=[
        "vid1.mp4",
        "vid2.mp4",
        "vid3.mp4",
    ],
)


def update_credit(amount: int):
    state.credit += amount
    with open(CREDIT_STORE_FILE, "w") as f:
        f.write(str(state.credit))


def on_button_press():
    if (state.name == StateName.COMMERICALS and state.credit >= CREDIT_FOR_BLOWING) or (
        state.name == StateName.RESULT
    ):
        state.name = StateName.CAN_BLOW
        state.credit -= CREDIT_FOR_BLOWING
        state.time_left = BLOWING_TIME
        state.alcohol = 0
        state.current_max = 0
        state.alcohol_result = 0
        state.image_path = None
        state.qr_path = None

    elif state.name == StateName.CAN_BLOW:
        state.name = StateName.BLOWING
        start_time_left_countdown()


def update_alcohol(amount: int):
    state.alcohol += amount
    if state.name == StateName.BLOWING:
        if state.alcohol > state.current_max:
            state.current_max = state.alcohol


def trigger_camera():
    pass


def process_camera_image(image_bytes: bytes):
    if state.name not in {StateName.BLOWING, StateName.RESULT}:
        return

    with open(CURRENT_BLOW_IMAGE_NAME, "wb") as f:
        f.write(image_bytes)

    state.image_path = CURRENT_BLOW_IMAGE_NAME


def generate_qr_code(blow_id: int) -> str:
    url = f"{PUBLIC_SERVER_URL}/blows/{blow_id}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill="black", back_color="white")

    image_name = f"qr_{blow_id}.png"
    img.save(image_name)
    return image_name


def start_time_left_countdown():
    def countdown():
        # take image halfway
        if state.time_left == BLOWING_TIME // 2:
            trigger_camera()

        if state.time_left <= 0:
            state.alcohol_result = state.current_max
            # TODO: UNCOMMENT
            # blow_id = store_result_to_server()
            # if blow_id is not None:
            #     state.qr_path = generate_qr_code(blow_id)
            #     shutil.copy(CURRENT_BLOW_IMAGE_NAME, f"image_{blow_id}.jpg")

            state.name = StateName.RESULT
            state.result_screen_time_left = RESULT_SCREEN_TIME
            start_result_screen_time_left_countdown()
            return

        state.blowing_time_left -= 1
        threading.Timer(1, countdown).start()

    countdown()


def start_result_screen_time_left_countdown():
    def countdown():
        if state.result_screen_time_left <= 0:
            state.name = StateName.COMMERICALS
            return

        state.result_screen_time_left -= 1
        threading.Timer(1, countdown).start()

    countdown()


def store_result_to_server() -> int | None:
    pass


class SimpleHandler(BaseHTTPRequestHandler):
    global state

    def do_GET(self):
        try:
            if self.path == "/":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(utils.to_json(state))
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            error_message = json.dumps({"error": str(e)})
            self.wfile.write(error_message.encode("utf-8"))


def tester():
    sleep(3)
    update_credit(50)
    sleep(3)
    update_credit(50)
    sleep(3)
    on_button_press()
    sleep(3)
    on_button_press()
    sleep(2)
    for i in range(BLOWING_TIME - 2):
        update_alcohol(10 * i)
        sleep(0.5)


if __name__ == "__main__":
    threading.Thread(target=tester).start()

    HTTPServer(("", 8000), SimpleHandler).serve_forever()
