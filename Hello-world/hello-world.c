#include "stm32f0xx.h"
#include "stdio.h"
#include "string.h"
#include "uart.h"
#include "sysid.h"

char filler[] = {1,2,3,9};
char empty[20];
char	buf_100[101];

uint32_t	xx1 = 0x12345678;
const uint32_t	xx2 = 0xfedcba98;

void delay1(int x)

{
  volatile int	z;

  z = x;
  while (z--) ;
}

const char	digit_to_hex[] = "0123456789abcdef";

char *
itoh(char *buf, uint32_t x)

{
  short	i;
  char	*p = buf;
  for(i = 7; i >= 0; i--) {
    *p++ = digit_to_hex[(x >> (i*4)) & 0x0f];
  }
  *p++ = 0;
  return buf;
}

typedef unsigned long	ulong;

void
write_flash(uint16_t *addr, uint16_t data)

{
  if ((FLASH->CR | FLASH_CR_LOCK)) {
    FLASH->KEYR = 0x45670123;
    FLASH->KEYR = 0xCDEF89AB;
  }

  FLASH->CR = FLASH->CR | FLASH_CR_PG;

  *addr = data;

  while (FLASH->SR & FLASH_SR_BSY)
    ;

  FLASH->CR = FLASH->CR | FLASH_CR_LOCK;
}

void
print_cpu_info(uint16_t uart)

{
  char	buf[100];
  int	i;

  for (i = 0; i < 3; i++) {
    buf_100[0] = 0;
    strcat(buf_100,"UID ");
    strcat(buf_100,itoh(buf,i)+7);
    strcat(buf_100,": ");
    strcat(buf_100,itoh(buf,UNIQUE_ID->UID[i]));
    strcat(buf_100,"\r\n");
    uart_send_str(uart,buf_100);
  }
  buf_100[0] = 0;
  strcat(buf_100,"MEMSIZE ");
  strcat(buf_100,itoh(buf,MEMSIZE)+4);
  strcat(buf_100,"\r\n");
  uart_send_str(uart,buf_100);
}


void
print_uint(uint16_t uart, uint32_t x, int ndigits)

{
  char	buf[10];
  uart_send_str(uart,itoh(buf,x)+(8-ndigits));
}

int
uart_idle(void *context)

{
  static uint32_t	counter;

  counter++;

  if ((counter & 0x03ffff) == 0) {
    if (counter & 0x40000) {
      GPIOA->BSRR = GPIO_BSRR_BS_9 | GPIO_BSRR_BR_10;
    } else {
      GPIOA->BSRR = GPIO_BSRR_BR_9 | GPIO_BSRR_BS_10;
    }
  }
  return 0;
}

int
main(argc,argv,envp)

int argc;
char **argv;
char **envp;

{

#if 0
  write_flash((uint16_t*)0x0800f000,0x1234);
  {
    int	i;
    uint16_t	*farr = (uint16_t *)0x0800f000;
    for (i = 0; i < 256; i++) {
      uint16_t	*p = &farr[i];
      if ((*p) & 0xf000) {
	write_flash(p,i);
	break;
      }
    }
  }

#endif

  RCC->AHBENR |= RCC_AHBENR_GPIOAEN | RCC_AHBENR_GPIOBEN;

  GPIOA->MODER = (GPIOA->MODER & ~GPIO_MODER_MODER14) | GPIO_MODER_MODER14_0;
  GPIOA->OTYPER = 0x00000000;
  GPIOA->OSPEEDR = GPIO_OSPEEDER_OSPEEDR14_0 | GPIO_OSPEEDER_OSPEEDR14_1;

  GPIOA->MODER = (GPIOA->MODER & ~GPIO_MODER_MODER9) | GPIO_MODER_MODER9_0;
  GPIOA->MODER = (GPIOA->MODER & ~GPIO_MODER_MODER10) | GPIO_MODER_MODER10_0;

  RCC->APB1ENR |= RCC_APB1ENR_USART2EN;

  uart_clear_settings(2);
  uart_set_speed(2,48000000,57600);
  uart_set_parity(2,UART_PARITY_EVEN);

  GPIOA->MODER &= ~GPIO_MODER_MODER14;
  GPIOA->MODER |= GPIO_MODER_MODER14_1;

  GPIOA->AFR[1] &= ~GPIO_AFRH_AFRH6;
  GPIOA->AFR[1] |= (1 << ((14-8)*4)); /* AF1 --> AFRH14 */

  GPIOA->MODER &= ~GPIO_MODER_MODER15;
  GPIOA->MODER |= GPIO_MODER_MODER15_1;

  GPIOA->AFR[1] &= ~GPIO_AFRH_AFRH7;
  GPIOA->AFR[1] |= (1 << ((15-8)*4)); /* AF1 --> AFRH15 */

  uart_set_wait_fun(uart_idle,0);

  uart_start(2);

  uart_send_str(2,"\r\nHello, world!\r\n");

  print_cpu_info(2);

  {
    char	buf[100];
    int		counter;
    int		c;
    while (1) {
      delay1(5);
      counter++;
      buf_100[0] = 0;
      strcat(buf_100,"Line ");
      strcat(buf_100,itoh(buf,counter));
      strcat(buf_100,"  ");
      uart_send_str(2,buf_100);
      strcpy(buf_100,"\r\n");
      while (((c = uart_get_char(2)) != '\r') &&
	     (c != '\n'))
	;
      uart_send_str(2,"\r\n");
    }
  }

}
