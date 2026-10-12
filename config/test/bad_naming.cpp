#include <cstdint>

namespace APP
{

static const uint16_t maxJump = 50U;

class battery_service
{
public:
    uint16_t GetSoc (void) const;

private:
    bool isPlausible (uint16_t soc) const;

    uint16_t lastSoc = 0U;
};

int GlobalCounter = 0;

uint16_t battery_service::GetSoc (void) const
{
    uint16_t SocValue = lastSoc;
    return SocValue;
}

bool battery_service::isPlausible (uint16_t soc) const
{
    return (soc <= maxJump);
}

} // namespace APP
