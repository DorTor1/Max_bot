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
    <Panel mode="secondary" className="box-border min-h-full h-full">
      <Flex
        direction="column"
        gap={16}
        className="mx-auto h-full min-h-full max-w-[560px] p-4"
      >
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
