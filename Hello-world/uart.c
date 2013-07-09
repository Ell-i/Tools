#include "uart.h"

static uart_wait_fun_ptr	wait_fun;
static void	*wait_context;

static USART_TypeDef *
uart_ptr(uint16_t uart)

{
  USART_TypeDef	*usart_ptr;

  switch (uart) {
  case 1: usart_ptr = USART1; break;
  default:
  case 2: usart_ptr = USART2; break;
  }
  return usart_ptr;
}

void
uart_clear_settings(uint16_t uart)

{
  USART_TypeDef	*usart_ptr = uart_ptr(uart);
  usart_ptr->CR1 = 0x00000000;
  usart_ptr->CR2 = 0x00000000;
  usart_ptr->CR3 = 0x00000000;
  usart_ptr->BRR = 0x00000000;
  usart_ptr->GTPR = 0x00000000;
  usart_ptr->RTOR = 0x00000000;
  usart_ptr->RQR = 0x00000000;
  usart_ptr->ICR = 0x00000000;
}

void
uart_start(uint16_t uart)

{
  USART_TypeDef	*usart_ptr = uart_ptr(uart);
  usart_ptr->CR1 |= USART_CR1_UE;
  usart_ptr->CR1 |= USART_CR1_TE | USART_CR1_RE;
}

uint32_t
uart_set_speed(uint16_t uart, uint32_t cpu_freq, uint32_t speed)

{
  uint32_t	divisor;
  USART_TypeDef	*usart_ptr = uart_ptr(uart);
  divisor = cpu_freq / speed;

  usart_ptr->CR1 &= ~USART_CR1_OVER8;
  usart_ptr->BRR = divisor;

  return divisor;
}

void
uart_set_parity(uint16_t uart, uint32_t parity)

{
  USART_TypeDef	*usart_ptr = uart_ptr(uart);

  usart_ptr->CR1 &= ~USART_CR1_UE;

  switch (parity) {
  case UART_PARITY_NONE:
    usart_ptr->CR1 &= ~(USART_CR1_PCE|USART_CR1_M);
    break;
  case UART_PARITY_EVEN:
    usart_ptr->CR1 |= USART_CR1_PCE | USART_CR1_M;
    usart_ptr->CR1 &= ~USART_CR1_PS;
    break;
  case UART_PARITY_ODD:
    usart_ptr->CR1 |= USART_CR1_PCE | USART_CR1_M;
    usart_ptr->CR1 |= ~USART_CR1_PS;
    break;
  }
}

int
uart_get_char(uint16_t uart)

{
  USART_TypeDef	*usart_ptr = uart_ptr(uart);
  int	c;

  while (!(usart_ptr->ISR & USART_ISR_RXNE))
    if (wait_fun) {
      if (wait_fun(wait_context))
	return -1;
    }

  c = usart_ptr->RDR & 0xff;
  return c;
}


void
uart_send_str(uint16_t uart, char *str)

{
  USART_TypeDef	*usart_ptr = uart_ptr(uart);
  unsigned char	*p = (unsigned char*)str;
  int	c;
  for( ; *p; p++) {
    while (!(usart_ptr->ISR & USART_ISR_TXE))
      if (wait_fun) {
	if (wait_fun(wait_context))
	  return -1;
      }
    usart_ptr->TDR = *p;
  }
  while (!(usart_ptr->ISR & USART_ISR_TXE)) ;
}

void
uart_set_wait_fun(uart_wait_fun_ptr fun, void *context)

{
  wait_fun = fun;
  wait_context = context;
}

