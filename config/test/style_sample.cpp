#include <cstdint>

namespace APP
{

enum class Result
{
    SUCCESS,
    FAIL
};

class BatteryService
{
public:
    /// @brief Reads the fuel gauge and stores the latest state of charge.
    /// @return Result::SUCCESS on a valid reading, Result::FAIL otherwise.
    Result update (void);

    uint16_t getSoc (void) const;

private:
    Result _readGauge (uint16_t *soc);
    bool _isPlausible (uint16_t soc) const;

    uint16_t last_soc_ = 0U;
};

BatteryService BATTERY_SERVICE;

static const uint16_t MAX_JUMP = 50U;

Result BatteryService::update (void)
{
    uint16_t soc = 0U;

    if (_readGauge(&soc) != Result::SUCCESS)
    {
        return Result::FAIL;
    }

    if (!_isPlausible(soc))
    {
        return Result::FAIL;
    }

    last_soc_ = soc;
    return Result::SUCCESS;
}

Result BatteryService::_readGauge (uint16_t *soc)
{
    *soc = 500U;
    return Result::SUCCESS;
}

bool BatteryService::_isPlausible (uint16_t soc) const
{
    uint16_t diff = (soc >= last_soc_) ? (soc - last_soc_) : (last_soc_ - soc);

    return ((soc <= 1000U) && (diff <= MAX_JUMP));
}

uint16_t BatteryService::getSoc (void) const
{
    return last_soc_;
}

void logState (const BatteryService &service);

} // namespace APP
