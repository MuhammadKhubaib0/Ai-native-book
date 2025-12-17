import React from 'react';
import clsx from 'clsx';
import styles from './HomepageFeatures.module.css';

const FeatureList = [
  {
    title: 'ROS 2 Fundamentals',
    Svg: require('../../static/img/robot-arm.svg').default,
    description: (
      <>
        Master the Robot Operating System fundamentals, nodes, topics, and
        services that form the backbone of robotic applications.
      </>
    ),
  },
  {
    title: 'Simulation & Perception',
    Svg: require('../../static/img/isaac-logo.svg').default,
    description: (
      <>
        Learn simulation techniques with Gazebo and Unity, and perception
        systems using computer vision and sensor fusion.
      </>
    ),
  },
  {
    title: 'Navigation & Control',
    Svg: require('../../static/img/navigation.svg').default,
    description: (
      <>
        Understand navigation systems using Nav2, motion planning, and
        humanoid robot control techniques.
      </>
    ),
  },
];

function Feature({Svg, title, description}) {
  return (
    <div className={clsx('col col--4', styles.featureCard)}>
      <div className="text--center">
        <Svg className={styles.featureSvg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}