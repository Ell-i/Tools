/*
 * Linker subscript for STM32F051 definitions with 64K Flash and 8K RAM
 * Copyright RAISONANCE 2007
 *
 * You can use, copy and distribute this file freely, but without any warranty.
 */

/* Memory Spaces Definitions */

ENTRY(Reset_Handler)

MEMORY
{
  FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 64K
  RAM  (xrw) : ORIGIN = 0x20000000, LENGTH = 8K
}

/* highest address of the user mode stack */
_estack = 0x20002000;
