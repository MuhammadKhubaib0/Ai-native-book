// @ts-check
const prismThemes = require('prism-react-renderer').themes;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Physical AI & Humanoid Robotics Textbook',
  tagline: 'An interactive, AI-native textbook teaching Physical AI & Humanoid Robotics',
  favicon: 'img/favicon.ico',

  // Updated URL and BaseURL for your specific GitHub Repository
  url: 'https://MuhammadKhubaib0.github.io',
  baseUrl: '/',
  organizationName: 'MuhammadKhubaib0', 
  projectName: 'Ai-native-book',
  trailingSlash: false,

  onBrokenLinks: 'warn',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  presets: [
    [
      'classic',
      /** @type {import('@docusaurus/preset-classic').Options} */
      ({
        docs: {
          sidebarPath: require.resolve('./sidebars.js'),
          editUrl: 'https://github.com/MuhammadKhubaib0/Ai-native-book/tree/main/',
        },
        blog: false, 
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      image: 'img/docusaurus-social-card.jpg',
      navbar: {
        title: 'Physical AI Textbook',
        logo: {
          alt: 'Physical AI & Humanoid Robotics Logo',
          src: 'img/logo.svg',
          width: 32,
          height: 32,
        },
        items: [
          {
            type: 'docSidebar',
            sidebarId: 'module1Sidebar',
            position: 'left',
            label: 'Module 1: ROS 2',
          },
          {
            type: 'docSidebar',
            sidebarId: 'module2Sidebar',
            position: 'left',
            label: 'Module 2: Gazebo & Unity',
          },
          {
            type: 'docSidebar',
            sidebarId: 'module3Sidebar',
            position: 'left',
            label: 'Module 3: NVIDIA Isaac',
          },
          {
            type: 'docSidebar',
            sidebarId: 'module4Sidebar',
            position: 'left',
            label: 'Module 4: VLA Capstone',
          },
          {
            href: 'https://github.com/MuhammadKhubaib0/Ai-native-book',
            label: 'GitHub',
            position: 'right',
          },
        ],
      },
      footer: {
        style: 'dark',
        links: [
          {
            title: 'Modules',
            items: [
              { label: 'Module 1: ROS 2', to: '/docs/module1-ros2/intro' },
              { label: 'Module 2: Gazebo & Unity', to: '/docs/module2-gazebo-unity/physics-simulation' },
              { label: 'Module 3: NVIDIA Isaac', to: '/docs/module3-isaac/isaac-sim/overview' },
              { label: 'Module 4: VLA', to: '/docs/module4-vla/voice-to-action' },
            ],
          },
          {
            title: 'Community',
            items: [
              { label: 'Stack Overflow', href: 'https://stackoverflow.com/questions/tagged/robotics' },
              { label: 'Discord', href: 'https://discordapp.com/invite/your-discord-invite' },
              { label: 'Twitter', href: 'https://twitter.com/your-twitter-handle' },
            ],
          },
          {
            title: 'More',
            items: [
              { label: 'GitHub', href: 'https://github.com/MuhammadKhubaib0/Ai-native-book' },
            ],
          },
        ],
        copyright: `Copyright © ${new Date().getFullYear()} Physical AI & Humanoid Robotics Textbook. Built with Docusaurus.`,
      },
      prism: {
        theme: prismThemes.github,
        darkTheme: prismThemes.dracula,
      },
    }),
};

module.exports = config;