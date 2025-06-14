# Daisyworld: A Visual Simulation

This project is an interactive, visual experiment based on James Lovelock's **Daisyworld model**, created with Python and the Pygame library. It provides a clear, hands-on demonstration of the core concepts of the **Gaia hypothesis**—the idea that life can collectively and unintentionally self-regulate its environment to maintain habitable conditions.

![Daisyworld Simulation Screenshot](./DaisyWorld_Screenshot.gif)

---

## The Concept

Daisyworld is a hypothetical planet orbiting a star whose energy output is slowly increasing over time. The only life on this planet are two species of daisies:

* **Black Daisies:** Absorb sunlight, which warms their local surroundings and the planet as a whole.
* **White Daisies:** Reflect sunlight, which cools their local surroundings and the planet.

Both species have the same optimal temperature for growth (22.5°C) and cannot survive if it gets too hot or too cold. The simulation demonstrates how the competition between these two species creates a feedback loop that stabilizes the planet's temperature, even as the sun grows hotter.

---

## Features

* **Interactive Simulation:** Watch the planet evolve in real-time.
* **Dynamic Graphing:** A live chart displays the populations of both daisy species and the average planetary temperature, clearly showing the regulatory effect.
* **Visual Planet Surface:** See the planet's surface change as the daisy populations shift.
* **Multiple States:** The simulation includes a start screen, a running state, and an end screen that automatically appears when the experiment concludes.
* **Clear Explanations:** On-screen panels and a detailed end screen explain the formulas, variables, and results of the experiment.

---

## How to Run

### Prerequisites

* Python 3.x
* Pygame library

### Installation

1.  **Install Python:** If you don't have Python, download it from [python.org](https://www.python.org/downloads/).

2.  **Install Pygame:** Open your terminal or command prompt and run the following command:
    ```bash
    pip install pygame
    ```

3.  **Run the Simulation:** Navigate to the project directory in your terminal and run the script:
    ```bash
    python daisyworld.py
    ```

---

## Controls

* **ENTER:** Start the simulation from the welcome screen.
* **SPACEBAR:** Pause or resume the running simulation.
* **R KEY:** Restart the experiment from any screen (start, simulation, or end).

---

## Simulation Phases

When you run the experiment, you will observe three distinct phases on the graph:

1.  **Warming Phase:** Initially, the planet is cold. The heat-absorbing **black daisies** thrive, and their population grows, warming the planet to a comfortable temperature.

2.  **Homeostasis (Regulation):** As the sun's energy increases, the planet gets warmer, giving the reflective **white daisies** an advantage. For a long period, the two populations dynamically balance each other out, keeping the planetary temperature remarkably stable. This is the Gaia effect in action.

3.  **Extinction (Heat Death):** Eventually, the sun becomes too hot for even the cooling effect of the white daisies. The temperature soars past their survival limit, causing a total collapse of all life and a rapid, unregulated spike in the planet's temperature.
