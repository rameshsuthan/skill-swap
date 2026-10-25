"""Controlled LLM boundary for integration tests. Domain/MCP/graph are always real."""

import json

from langchain_core.messages import AIMessage


class ControlledModel:
    def __init__(self, quota=False, reject_once=False, ambiguous=False):
        self.quota = quota
        self.reject_once = reject_once
        self.ambiguous = ambiguous
        self.reviewer_outage = False
        self.tools = []
        self.schema = None

    def bind_tools(self, tools, **kwargs):
        self.tools = tools
        self.schema = None
        return self

    def with_structured_output(self, schema, **kwargs):
        self.schema = schema
        return self

    async def ainvoke(self, messages):
        if self.quota:
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        payload = json.loads(messages[1].content)
        if "simulate quota" in payload.get("request", "").lower():
            raise RuntimeError("429 RESOURCE_EXHAUSTED")
        role = payload["role"]
        if role == "interpreter":
            self.reviewer_outage = "simulate reviewer outage" in payload.get("request", "").lower()
        if role == "reviewer" and self.reviewer_outage:
            raise RuntimeError("503 UNAVAILABLE")
        results = [json.loads(m.content) for m in messages if m.type == "tool"]
        if self.schema:
            if role == "interpreter":
                if self.ambiguous and "clarification:" not in payload["request"]:
                    return self.schema(goal=None, clarification="Which skill: Python or SQL?")
                request = payload["request"].lower()
                skill = (
                    "excel_automation"
                    if "excel" in request
                    else "sql"
                    if "sql" in request
                    else "presentation_design"
                )
                return self.schema(
                    goal={"skill_id": skill, "minimum_teacher_proficiency": 2}, clarification=None
                )
            if role == "coordinator":
                plans = next(r["plans"] for r in results if "plans" in r)
                return self.schema(
                    fingerprint=plans[0]["fingerprint"] if plans else None,
                    summary="Declared skills form a reciprocal exchange."
                    if plans
                    else "No feasible exchange.",
                )
            reject = self.reject_once
            self.reject_once = False
            return self.schema(
                accepted=not reject,
                summary="Independent schedule and profile review passed."
                if not reject
                else "Investigate another time.",
            )
        tool = self.tools[0]["function"]["name"]
        if tool == "get_learning_context":
            args = {}
        elif tool == "search_memories":
            args = {"query": "teaching and learning preferences"}
        elif tool in ("search_teachers", "find_exchange_cycles"):
            args = {"goal": payload["goal"]}
            if tool == "find_exchange_cycles":
                preferences = " ".join(
                    m["text"] for m in payload.get("remembered_preferences", [])
                ).lower()
                style = (
                    "guided_project"
                    if "guided" in preferences
                    else "discussion"
                    if "discussion" in preferences
                    else None
                )
                teachers = next(r["teachers"] for r in results if "teachers" in r)
                args["preferred_member_ids"] = [
                    t["id"] for t in teachers if style in t["offer"]["styles"]
                ]
        else:
            args = {k: payload["plan"][k] for k in ("cycle", "goal")}
            args["proposed_sessions"] = payload["plan"]["sessions"]
        return AIMessage(
            content="",
            tool_calls=[
                {"name": tool, "args": args, "id": f"call-{len(results)}", "type": "tool_call"}
            ],
        )
