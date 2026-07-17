'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowRight, Download, Play, Shield, Zap, Activity } from 'lucide-react'
import { siteConfig } from '@/lib/site'

export function Hero() {
  return (
    <section className="relative pt-32 pb-16 sm:pt-40 sm:pb-24 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-mc-50/50 to-white dark:from-mc-950/20 dark:to-surface-950" />
      <div className="absolute top-20 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-mc-500/10 rounded-full blur-3xl" />

      <div className="container-wide relative">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-mc-200 dark:border-mc-800 bg-mc-50 dark:bg-mc-950/50 text-mc-700 dark:text-mc-300 text-sm font-medium mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-mc-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-mc-500" />
              </span>
              Version 3.0 Now Available
            </div>
          </motion.div>

          <motion.h1
            className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight text-balance mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            Enterprise IT Operations{' '}
            <span className="gradient-text">Platform</span>
          </motion.h1>

          <motion.p
            className="text-lg sm:text-xl text-surface-500 dark:text-surface-400 max-w-2xl mx-auto mb-10 text-balance"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            {siteConfig.description} One platform to monitor, manage, automate, and secure your entire IT infrastructure.
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Link
              href={siteConfig.links.download}
              className="btn-primary text-base py-3 px-8"
            >
              <Download className="w-5 h-5" />
              Download Free
            </Link>
            <Link
              href={siteConfig.links.demo}
              className="btn-secondary text-base py-3 px-8"
            >
              <Play className="w-5 h-5" />
              Live Demo
            </Link>
            <Link
              href="/documentation"
              className="btn-ghost text-base py-3 px-8"
            >
              Documentation
              <ArrowRight className="w-4 h-4" />
            </Link>
          </motion.div>
        </div>

        <motion.div
          className="relative max-w-5xl mx-auto"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.4 }}
        >
          <div className="rounded-2xl border border-gray-200 dark:border-gray-800 shadow-2xl shadow-mc-500/10 overflow-hidden bg-white dark:bg-surface-900">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 dark:border-gray-800 bg-surface-50 dark:bg-surface-800">
              <div className="flex gap-1.5">
                <div className="w-3 h-3 rounded-full bg-red-400" />
                <div className="w-3 h-3 rounded-full bg-yellow-400" />
                <div className="w-3 h-3 rounded-full bg-green-400" />
              </div>
              <div className="flex-1 text-center">
                <span className="text-xs text-surface-400">Mission Control Dashboard</span>
              </div>
            </div>
            <div className="aspect-video bg-gradient-to-br from-surface-50 to-surface-100 dark:from-surface-900 dark:to-surface-800 flex items-center justify-center">
              <div className="grid grid-cols-3 gap-4 p-8 w-full max-w-3xl">
                <div className="col-span-2 rounded-xl bg-white dark:bg-surface-700 p-6 shadow-sm border border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-2 mb-4">
                    <Activity className="w-5 h-5 text-mc-500" />
                    <span className="text-sm font-semibold">Infrastructure Overview</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {[
                      { label: 'Nodes', value: '1,247', icon: '🟢' },
                      { label: 'Alerts', value: '3', icon: '🟡' },
                      { label: 'Uptime', value: '99.99%', icon: '🟢' },
                    ].map((item) => (
                      <div key={item.label} className="p-3 rounded-lg bg-surface-50 dark:bg-surface-600">
                        <div className="text-xs text-surface-500">{item.label}</div>
                        <div className="text-lg font-bold mt-1">
                          {item.icon} {item.value}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="rounded-xl bg-white dark:bg-surface-700 p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <Shield className="w-4 h-4 text-green-500" />
                      <span className="text-xs font-semibold">Security</span>
                    </div>
                    <div className="text-sm font-bold text-green-600">All Clear</div>
                  </div>
                  <div className="rounded-xl bg-white dark:bg-surface-700 p-4 shadow-sm border border-gray-100 dark:border-gray-700">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-4 h-4 text-mc-500" />
                      <span className="text-xs font-semibold">Automation</span>
                    </div>
                    <div className="text-sm font-bold">24 Running</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div className="absolute -inset-4 bg-gradient-to-r from-mc-500/5 via-transparent to-mc-500/5 rounded-3xl -z-10" />
        </motion.div>
      </div>
    </section>
  )
}
