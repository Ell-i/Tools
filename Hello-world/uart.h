#ifndef __UART_H__
#define __UART_H__ 1

#include "stm32f0xx.h"

extern void
uart_clear_settings(uint16_t uart);

extern uint32_t
uart_set_speed(uint16_t uart, uint32_t cpu_freq, uint32_t speed);

extern void
uart_send_str(uint16_t uart, char *str);

extern void
uart_start(uint16_t uart);

extern int
uart_get_char(uint16_t uart);

#define UART_PARITY_NONE	0
#define UART_PARITY_EVEN	1
#define UART_PARITY_ODD		2

extern void
uart_set_parity(uint16_t uart, uint32_t parity);

typedef int (*uart_wait_fun_ptr)(void *context);

extern void
uart_set_wait_fun(uart_wait_fun_ptr fun, void *context);

#endif /*  __UART_H__ */
