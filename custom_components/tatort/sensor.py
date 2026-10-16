
"""Sensor platform for Tatort."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TatortCoordinator
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class TatortSensorDescription(SensorEntityDescription):
    """Describe a Tatort sensor."""

    data_key: str


SENSORS: tuple[TatortSensorDescription, ...] = (
    TatortSensorDescription(
        key="aktuell",
        name="Tatort Aktuell",
        icon="mdi:pistol",
        data_key="aktuell",
    ),
    TatortSensorDescription(
        key="stadt",
        name="Tatort Stadt",
        icon="mdi:map-marker",
        data_key="stadt",
    ),
    TatortSensorDescription(
        key="titel",
        name="Tatort Titel",
        icon="mdi:movie-open",
        data_key="titel",
    ),
    TatortSensorDescription(
        key="ermittler",
        name="Tatort Ermittler",
        icon="mdi:account-search",
        data_key="ermittler",
    ),
    TatortSensorDescription(
        key="folgen_id",
        name="Tatort Folgen ID",
        icon="mdi:identifier",
        data_key="folgen_id",
    ),
    TatortSensorDescription(
        key="bild_api",
        name="Tatort Bild API",
        icon="mdi:image",
        data_key="bild_api",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tatort sensors."""
    coordinator: TatortCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        TatortSensor(coordinator, description)
        for description in SENSORS
    )


class TatortSensor(CoordinatorEntity[TatortCoordinator], SensorEntity):
    """Represent a Tatort data field."""

    entity_description: TatortSensorDescription
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: TatortCoordinator,
        description: TatortSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"tatort_{description.key}"

    @property
    def native_value(self) -> str:
        """Return the sensor value."""
        return self.coordinator.data.get(
            self.entity_description.data_key,
            "unbekannt",
        )
