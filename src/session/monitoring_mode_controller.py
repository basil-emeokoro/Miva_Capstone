from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitoringModePlan:
    mode: str
    enabled_modules: list[str]
    disabled_modules: list[str]
    confidence_note: str


class MonitoringModeController:
    def configure(self, selected_mode: str) -> MonitoringModePlan:
        mode = selected_mode.upper()
        if mode == "A":
            return MonitoringModePlan(
                mode="A",
                enabled_modules=["primary_camera", "audio", "behaviour", "identity"],
                disabled_modules=["secondary_camera", "room_object_detection", "environmental_fusion"],
                confidence_note="Single-camera CBT mode uses stronger identity and behaviour checks due to limited room visibility.",
            )
        if mode == "B":
            return MonitoringModePlan(
                mode="B",
                enabled_modules=["primary_camera", "secondary_camera", "audio", "behaviour", "identity", "event_fusion"],
                disabled_modules=[],
                confidence_note="Dual-camera mode is the recommended full monitoring mode.",
            )
        if mode == "C":
            return MonitoringModePlan(
                mode="C",
                enabled_modules=["primary_camera", "mirror_support", "audio", "behaviour", "identity"],
                disabled_modules=["high_confidence_reflected_object_detection"],
                confidence_note="Mirror mode is a low-resource fallback; reflected object evidence is weighted conservatively.",
            )
        raise ValueError(f"Unsupported monitoring mode: {selected_mode}")
