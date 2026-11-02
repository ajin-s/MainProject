"""
Facial Bitmap Generator for 8 Emotion States of SmartEduSync Robot.
Vocabulary: idle, watching, listening, thinking, curious, happy, concerned, alert.
"""
from typing import Dict

FACE_BITMAPS: Dict[str, str] = {
    "idle": (
        "    ( - )        ( - )    \n"
        "                          \n"
        "         -------          "
    ),
    "watching": (
        "    ( O )        ( O )    \n"
        "                          \n"
        "         =======          "
    ),
    "listening": (
        "    ( ^ )        ( ^ )    \n"
        "      |            |      \n"
        "         -------          "
    ),
    "thinking": (
        "    ( > )        ( < )    \n"
        "            ?             \n"
        "         - - - -          "
    ),
    "curious": (
        "   / ( o ) \\    / ( O ) \\\n"
        "            ?             \n"
        "         (  o  )          "
    ),
    "happy": (
        "    ( ^ )        ( ^ )    \n"
        "          \\____/          \n"
        "         \\______/         "
    ),
    "concerned": (
        "    ( - )        ( - )    \n"
        "     /            \\       \n"
        "         /------\\         "
    ),
    "alert": (
        "   ! ( O ) !    ! ( O ) !\n"
        "          !!!!!!          \n"
        "         [======]         "
    ),
}


def get_face_art(emotion: str) -> str:
    return FACE_BITMAPS.get(emotion.lower(), FACE_BITMAPS["idle"])


if __name__ == "__main__":
    for emo in FACE_BITMAPS:
        print(f"=== {emo.upper()} ===")
        print(get_face_art(emo))
        print()
