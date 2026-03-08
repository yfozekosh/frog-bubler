from typing import Protocol, Any, List


class DeviceInfo(Protocol):
    device_on: bool


class CurrentPower(Protocol):
    current_power: float


class EnergyDataResult(Protocol):
    data: List[float]


class P110Device(Protocol):
    async def get_device_info(self) -> DeviceInfo: ...

    async def get_current_power(self) -> CurrentPower: ...

    async def get_energy_data(self, interval: Any, start_date: Any = ...) -> EnergyDataResult: ...

    async def on(self) -> None: ...

    async def off(self) -> None: ...


class ApiClient:
    def __init__(self, username: str, password: str) -> None: ...

    async def p110(self, ip: str) -> P110Device: ...
