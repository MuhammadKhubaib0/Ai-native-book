// @ts-check
// Note: type annotations allow type checking and IDEs autocompletion

const prismThemes = require('prism-react-renderer').themes;

/** @type {import('@docusaurus/types').Config} */
const config = {
  title: 'Physical AI & Humanoid Robotics Textbook',
  tagline: 'An interactive, AI-native textbook teaching Physical AI & Humanoid Robotics',
  favicon: 'img/favicon.ico',

  // Set the production url of your site here
  url: 'https://your-book-url.com',
  // Set the /<base>/ pathname under which your site is served
  // For GitHub Pages deployment, this is often '/<projectName>/'
  baseUrl: '/physical-ai-textbook/',

  // GitHub pages deployment config.
  organizationName: 'your-org', // Usually your GitHub org/user name.
  projectName: 'physical-ai-textbook', // Usually your repo name.

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  // Even if you don't use internalization, you can use this field to set useful
  // metadata like html lang. For example, if your site is Chinese, you may want
  // to replace "en" with "zh-Hans".
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
          // Please change this to your repo.
          // Remove this to remove the "edit this page" links.
          editUrl:
            'https://github.com/facebook/docusaurus/tree/main/packages/create-docusaurus/templates/shared/',
        },
        blog: false, // Disable blog if not needed
        theme: {
          customCss: require.resolve('./src/css/custom.css'),
        },
      }),
    ],
  ],

  themeConfig:
    /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
    ({
      // Replace with your project's social card
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
            href: 'https://github.com/your-org/physical-ai-textbook',
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
              {
                label: 'Module 1: ROS 2',
                to: '/docs/module1-ros2/intro',
              },
              {
                label: 'Module 2: Gazebo & Unity',
                to: '/docs/module2-gazebo-unity/physics-simulation',
              },
              {
                label: 'Module 3: NVIDIA Isaac',
                to: '/docs/module3-isaac/intro',
              },
              {
                label: 'Module 4: VLA',
                to: '/docs/module4-vla/intro',
              },
            ],
          },
          {
            title: 'Community',
            items: [
              {
                label: 'Stack Overflow',
                href: 'https://stackoverflow.com/questions/tagged/robotics',
              },
              {
                label: 'Discord',
                href: 'https://discordapp.com/invite/your-discord-invite',
              },
              {
                label: 'Twitter',
                href: 'https://twitter.com/your-twitter-handle',
              },
            ],
          },
          {
            title: 'More',
            items: [
              {
                label: 'GitHub',
                href: 'https://github.com/your-org/physical-ai-textbook',
              },
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