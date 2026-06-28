# Copyright (c) 2026 Russell Shen. All rights reserved.
#
# This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
# 4.0 International (CC BY-NC-ND 4.0) license.

import pytest
from fastapi.testclient import TestClient
from web.server import app, init_adventure_game, adventure_world_model

@pytest.fixture(autouse=True)
def reset_game():
    init_adventure_game()
    yield

def test_adventure_game_lifecycle():
    client = TestClient(app)
    
    # 1. Reset endpoint
    reset_res = client.post("/api/adventure/reset")
    assert reset_res.status_code == 200
    state = reset_res.json()["state"]
    assert state["chest_opened"] is False
    assert state["has_key"] is False
    assert state["gate_unlocked"] is False
    assert state["escaped"] is False

    # 2. Attempt unlock without key (should fail and revert)
    unlock_fail = client.post("/api/adventure/command", json={"text": "The hero unlocks the metal_gate"})
    assert unlock_fail.status_code == 200
    assert "You need a key to unlock" in unlock_fail.json()["message"]
    assert unlock_fail.json()["state"]["gate_unlocked"] is False

    # 3. Attempt exit locked gate (should fail and revert)
    exit_fail = client.post("/api/adventure/command", json={"text": "The hero exits the start_room"})
    assert exit_fail.status_code == 200
    assert "gate is locked" in exit_fail.json()["message"]
    assert exit_fail.json()["state"]["escaped"] is False

    # 4. Open chest (should trigger rule and give key)
    open_chest = client.post("/api/adventure/command", json={"text": "The hero opens the wooden_chest"})
    assert open_chest.status_code == 200
    assert "Inside, you find a golden key" in open_chest.json()["message"]
    assert open_chest.json()["state"]["has_key"] is True
    assert open_chest.json()["state"]["chest_opened"] is True

    # 5. Unlock gate with key (should succeed)
    unlock_ok = client.post("/api/adventure/command", json={"text": "The hero unlocks the metal_gate"})
    assert unlock_ok.status_code == 200
    assert "gate unlocks" in unlock_ok.json()["message"]
    assert unlock_ok.json()["state"]["gate_unlocked"] is True

    # 6. Exit unlocked gate (should win)
    exit_ok = client.post("/api/adventure/command", json={"text": "The hero exits the start_room"})
    assert exit_ok.status_code == 200
    assert "escaped" in exit_ok.json()["message"]
    assert exit_ok.json()["state"]["escaped"] is True
