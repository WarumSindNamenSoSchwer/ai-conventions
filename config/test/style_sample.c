#include "style_sample.h"

#include <stddef.h>

static uint16_t SAMPLE_BUFFER[BATTERY_MAX_SAMPLES];
static uint8_t SAMPLE_COUNT = 0U;

static int32_t _readRegister (uint8_t reg, uint16_t *value)
{
    const uint8_t SHIFT = 8U;
    uint8_t raw[2] = {0U, 0U};

    if (value == NULL)
    {
        return -1;
    }

    raw[0] = reg;
    *value = (uint16_t)(((uint16_t)raw[1] << SHIFT) | raw[0]);
    return 0;
}

static uint16_t _average (void)
{
    uint32_t sum = 0U;

    for (uint8_t i = 0U; ((i < SAMPLE_COUNT) && (i < BATTERY_MAX_SAMPLES)); i++)
    {
        sum += SAMPLE_BUFFER[i];
    }

    return (SAMPLE_COUNT > 0U) ? (uint16_t)(sum / SAMPLE_COUNT) : 0U;
}

int32_t batteryReadState (BatteryState *state)
{
    uint16_t soc = 0U;

    if (state == NULL)
    {
        return -1;
    }

    if ((_readRegister(0x02U, &soc) != 0) || (soc > 1000U))
    {
        return -2;
    }

    state->soc_permille = soc;
    state->voltage_mv = _average();
    return 0;
}
