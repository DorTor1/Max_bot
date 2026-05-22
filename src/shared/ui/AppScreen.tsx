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
    <Panel mode="secondary" style={{ minHeight: '100%', boxSizing: 'border-box' }}>
      <Flex direction="column" gap={16} style={{ padding: 16, maxWidth: 560, margin: '0 auto' }}>
        <Typography.Headline>{title}</Typography.Headline>
        <Flex direction="column" gap={12} style={{ flex: 1 }}>
          {children}
        </Flex>
        {footer ? (
          <Flex direction="column" gap={8}>
            {footer}
          </Flex>
        ) : null}
      </Flex>
    </Panel>
  )
}
