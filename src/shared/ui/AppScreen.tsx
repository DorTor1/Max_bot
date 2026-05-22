import { Flex, Panel, Typography } from '@maxhub/max-ui'
import type { ReactNode } from 'react'

export function AppScreen({
  title,
  children,
  footer,
}: {
  title: string
  children: ReactNode
  footer?: ReactNode
}) {
  return (
    <Panel
      mode="secondary"
      style={{
        boxSizing: 'border-box',
        minHeight: '100vh',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        margin: 0,
        padding: 0,
      }}
    >
      <Flex
        direction="column"
        gap={16}
        style={{
          width: '100%',
          maxWidth: '560px',
          padding: '16px',
          boxSizing: 'border-box',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          margin: '0 auto',
        }}
      >
        <Typography.Headline>{title}</Typography.Headline>
        <Flex direction="column" gap={12} style={{ flex: 1, display: 'flex', flexDirection: 'column', width: '100%' }}>
          {children}
        </Flex>
        {footer ? (
          <Flex direction="column" gap={8} style={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
            {footer}
          </Flex>
        ) : null}
      </Flex>
    </Panel>
  )
}
