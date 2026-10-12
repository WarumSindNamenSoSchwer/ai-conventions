#ifndef STYLE_SAMPLE_H
#define STYLE_SAMPLE_H

#include <stdint.h>

#define BATTERY_MAX_SAMPLES (16U)

typedef enum
{
    STATE_IDLE,
    STATE_MEASURING
} BatteryMode;

typedef struct
{
    uint16_t soc_permille;
    uint16_t voltage_mv;
} BatteryState;

int32_t batteryReadState (BatteryState *state);

#endif /* STYLE_SAMPLE_H */
