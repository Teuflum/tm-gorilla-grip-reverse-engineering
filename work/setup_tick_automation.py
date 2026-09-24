"""Create a separate TICK collection and load the known baseline inputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tick_client import TickClient, encoded


sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "work/tick_automation_state.json"
BASELINE = ROOT / "outputs/TICK_baseline_right.txt"
MAP_UID = "xsBIINZa10KzKOtrSt_oxEAnHX5"


def main() -> None:
    client = TickClient()
    status = client.get("runtime/status")
    settings = client.get("settings")
    if status["currentMapUid"] != MAP_UID:
        raise RuntimeError("Wrong map is loaded in Trackmania")
    if STATE.exists():
        state = json.loads(STATE.read_text(encoding="utf-8"))
        collection = client.get(f"input-collections/{state['collection_id']}")
        print("Existing automation collection:", collection["node"]["name"])
    else:
        state = {
            "original_collection_id": settings["activeInputCollectionId"],
            "original_loaded_revision_id": status["loadedInputRevisionId"],
        }
        created = client.post("input-collections", {
            "parentId": None,
            "name": "Gorilla Grip Auto Tests",
            "mapUid": MAP_UID,
            "mapName": "ANGULAR ↻ MOMENTUM",
        })
        state["collection_id"] = created["node"]["id"] if "node" in created else created["id"]
        STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        collection = client.get(f"input-collections/{state['collection_id']}")
        print("Created automation collection:", state["collection_id"])

    source = BASELINE.read_text(encoding="utf-8")
    current_id = collection.get("currentRevisionId")
    query = f"expectedBaseRevisionId={encoded(current_id)}&origin=ui" if current_id else "origin=ui"
    result = client.post(
        f"input-collections/{encoded(state['collection_id'])}/revisions?{query}",
        source,
        raw=True,
    )
    print("Created baseline revision:", result)
    collection = client.get(f"input-collections/{state['collection_id']}")
    revision_id = collection["currentRevisionId"]
    settings = client.get("settings")
    patched = client.patch("settings", {
        "expectedRevision": settings["revision"],
        "activeInputCollectionId": state["collection_id"],
    })
    print("Set active collection; settings revision:", patched.get("revision"))
    collection = client.get(f"input-collections/{state['collection_id']}")
    loaded = client.post(
        f"input-revisions/{revision_id}/load?expectedCollectionRevision={collection['node']['revision']}"
    )
    print("Loaded baseline revision:", loaded)
    status = client.get("runtime/status")
    print("Runtime:", {
        "loadedInputRevisionId": status["loadedInputRevisionId"],
        "loadedActionCount": status["loadedActionCount"],
        "lastErrorCode": status["lastErrorCode"],
    })
    state["baseline_revision_id"] = revision_id
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
