#ifndef __SYSID_H__
#define __SYSID_H__ 1

typedef struct
{
  __IO uint32_t UID[3];             /* Wafer X & Y                        Address offset: 0x00 */
  				    /* Lot & Wafer                        Address offset: 0x04 */
  				    /* Lot number                         Address offset: 0x08 */
} UID_TypeDef;

#define UID_BASE	((uint32_t)0x1FFFF7AC)
#define UNIQUE_ID	((UID_TypeDef *)UID_BASE)

#define MEMSIZE		(*((uint16_t*)0x1FFFF7CC))

#endif
