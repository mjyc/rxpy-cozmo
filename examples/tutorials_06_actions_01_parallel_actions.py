# https://github.com/anki/cozmo-python-sdk/blob/master/examples/tutorials/06_actions/01_parallel_actions.py

import rx
import rx.operators as ops

try:
    from PIL import Image
except ImportError:
    sys.exit(
        "Cannot import from PIL: Do `pip3 install --user Pillow` to install"
    )

import cozmo
from cozmo.util import degrees, distance_mm, speed_mmps

# load an image to display on Cozmo's face
face_image = Image.open("./cozmosdk.png")
# resize to fit on Cozmo's face screen
face_image = face_image.resize(cozmo.oled_face.dimensions(), Image.BICUBIC)
# convert the image to the format used by the oled screen
face_image = cozmo.oled_face.convert_image_to_screen_data(
    face_image, invert_image=True
)


def main(sources):
    example1_completed = rx.combine_latest(
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example1_set_head_angle")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example1_set_lift_height")
        ),
    )
    example2_completed = rx.combine_latest(
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example2_drive_straight")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example2_turn_in_place")
        ),
    )
    example3_completed = rx.combine_latest(
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example3_set_lift_height")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example3_set_head_angle")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example3_drive_straight")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example3_display_oled_face_image")
        ),
    )
    example4_completed = rx.combine_latest(
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example4_set_lift_height")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example4_set_head_angle")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example4_drive_straight")
        ),
        sources["Cozmo"].pipe(
            ops.filter(lambda i: i["id"] is "example4_display_oled_face_image")
        ),
    )
    example1_completed.subscribe(on_next=lambda i: print("example1_completed"))
    example2_completed.subscribe(on_next=lambda i: print("example2_completed"))
    example3_completed.subscribe(on_next=lambda i: print("example3_completed"))
    example4_completed.subscribe(on_next=lambda i: print("example4_completed"))
    rxcozmo = rx.merge(
        # example1_lift_head
        rx.of(
            {
                "id": "example1_set_head_angle",
                "name": "set_head_angle",
                "value": cozmo.robot.MAX_HEAD_ANGLE,
            }
        ),
        rx.of(
            {
                "id": "example1_set_lift_height",
                "name": "set_lift_height",
                "value": 1.0,
            }
        ),
        # example2_conflicting_actions
        example1_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example2_drive_straight",
                    "name": "drive_straight",
                    "value": {
                        "distance": distance_mm(50),
                        "speed": speed_mmps(25),
                        "should_play_anim": False,
                    },
                }
            )
        ),
        example1_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example2_turn_in_place",
                    "name": "turn_in_place",
                    "value": {"angle": degrees(90),},
                }
            )
        ),
        # example3_abort_one_action
        example2_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example3_set_lift_height",
                    "name": "set_lift_height",
                    "value": 0,
                }
            )
        ),
        example2_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example3_set_head_angle",
                    "name": "set_head_angle",
                    "value": {
                        "angle": cozmo.robot.MIN_HEAD_ANGLE,
                        "duration": 6.0,
                    },
                }
            )
        ),
        example2_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example3_drive_straight",
                    "name": "drive_straight",
                    "value": {
                        "distance": distance_mm(75),
                        "speed": speed_mmps(25),
                        "should_play_anim": False,
                    },
                }
            )
        ),
        example2_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example3_display_oled_face_image",
                    "name": "display_oled_face_image",
                    "value": {
                        "screen_data": face_image,
                        "duration_ms": 30000.0,
                    },
                }
            )
        ),
        # abort actions
        example2_completed.pipe(
            ops.map(lambda i: {"type": "abort", "name": "set_lift_height"})
        ),
        example2_completed.pipe(
            ops.delay(0.1),
            ops.map(lambda i: {"type": "abort", "name": "set_head_angle"}),
        ),
        example2_completed.pipe(
            ops.delay(2),
            ops.map(
                lambda i: {"type": "abort", "name": "display_oled_face_image"}
            ),
        ),
        # example4_abort_all_actions
        example3_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example4_set_lift_height",
                    "name": "set_lift_height",
                    "value": 0.0,
                }
            )
        ),
        example3_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example4_set_head_angle",
                    "name": "set_head_angle",
                    "value": {
                        "angle": cozmo.robot.MIN_HEAD_ANGLE,
                        "duration": 6.0,
                    },
                }
            )
        ),
        example3_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example4_drive_straight",
                    "name": "drive_straight",
                    "value": {
                        "distance": distance_mm(75),
                        "speed": speed_mmps(25),
                        "should_play_anim": False,
                    },
                }
            )
        ),
        example3_completed.pipe(
            ops.map(
                lambda i: {
                    "id": "example4_display_oled_face_image",
                    "name": "display_oled_face_image",
                    "value": {
                        "screen_data": face_image,
                        "duration_ms": 30000.0,
                    },
                }
            )
        ),
        # abort all actions
        example3_completed.pipe(
            ops.delay(2),
            ops.map(lambda i: {"type": "abort", "name": "set_lift_height"}),
        ),
        example3_completed.pipe(
            ops.delay(2),
            ops.map(lambda i: {"type": "abort", "name": "set_head_angle"}),
        ),
        example3_completed.pipe(
            ops.delay(2),
            ops.map(lambda i: {"type": "abort", "name": "drive_straight"}),
        ),
        example3_completed.pipe(
            ops.delay(2),
            ops.map(
                lambda i: {"type": "abort", "name": "display_oled_face_image"}
            ),
        ),
    )
    sinks = {"Cozmo": rxcozmo}
    return sinks
