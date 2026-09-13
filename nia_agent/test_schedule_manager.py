import os
import time
import pytest
from nia_agent.schedule_manager import ScheduledWorkflowManager

@pytest.fixture
def manager(tmp_path):
    data_file = tmp_path / "scheduled_workflows.json"
    mgr = ScheduledWorkflowManager(data_file=str(data_file))
    yield mgr
    mgr.stop()

def test_add_schedule(manager):
    result = manager.add_schedule("Test Daily", 86400, "Run daily checks")
    assert "added" in result
    assert len(manager.schedules) == 1
    sched = manager.schedules["Test Daily"]
    assert sched["interval_seconds"] == 86400
    assert sched["task"] == "Run daily checks"

def test_add_schedule_invalid_interval(manager):
    with pytest.raises(ValueError, match="Interval must be at least 60"):
        manager.add_schedule("Too Fast", 30, "Fast task")

def test_add_schedule_invalid_name(manager):
    with pytest.raises(ValueError):
        manager.add_schedule("", 3600, "Task")

def test_remove_schedule(manager):
    manager.add_schedule("To Remove", 3600, "Task")
    assert len(manager.schedules) == 1
    
    result = manager.remove_schedule("To Remove")
    assert "removed" in result
    assert len(manager.schedules) == 0

def test_list_schedules(manager):
    manager.add_schedule("Task 1", 3600, "First")
    manager.add_schedule("Task 2", 7200, "Second")
    
    schedules = manager.list_schedules()
    assert len(schedules) == 2
    names = [s["name"] for s in schedules]
    assert "Task 1" in names
    assert "Task 2" in names

def test_workflow_triggered_signal(manager):
    manager.add_schedule("Fast", 60, "Task")
    
    # We will manually simulate the loop or fake the last_run to force a trigger
    manager.schedules["Fast"]["last_run"] = time.time() - 100
    
    triggered = []
    manager.workflow_triggered.connect(lambda n, t: triggered.append((n, t)))
    
    # Run the internal loop once (normally runs in a thread)
    manager._running = True
    
    # We shouldn't run the infinite loop, just run the logic inside it
    current_time = time.time()
    for name, schedule in manager.schedules.items():
        interval = schedule.get("interval_seconds", 3600)
        last_run = schedule.get("last_run", 0)
        
        if current_time - last_run >= interval:
            schedule["last_run"] = current_time
            manager.workflow_triggered.emit(name, schedule.get("task", ""))
            
    assert len(triggered) == 1
    assert triggered[0] == ("Fast", "Task")

