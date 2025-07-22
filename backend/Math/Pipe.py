import numpy as np
from math import log10
class PipeModel:
    def __init__(self):
        # Геометрия трубы
        self.L = 5.0  # Длина [m]
        self.S = 0.01  # Площадь поперечного сечения [m^2]
        self.D_h = 0.1128  # Гидравлический диаметр [m]

        # Параметры для расчёта потерь давления
        self.L_eq = 1.0  # Equivalent length of local resistances [m]
        self.r = 15e-6  # Internal surface roughness [m]
        self.Re_lam = 2000  # Laminar flow upper Reynolds number
        self.Re_tur = 4000  # Turbulent flow lower Reynolds number
        self.lambda_lam = 64  # Laminar friction constant (Darcy friction factor)
        # Входные/Выходные давления
        self.p_in = 0
        self.p_out = 0
        # Температура в трубе
        self.T = 0
    def compute_reynolds(self, m_dot, mu, rho):
        """Вспомогательная функция для расчёта потерей давления """
        velocity = abs(m_dot) / (rho * self.S)
        Re = (rho * velocity * self.D_h) / mu
        return Re

    def compute_darcy_friction(self, Re):
        """Вспомогательная функция для расчёта потерей давления"""
        if Re < self.Re_lam:
            return self.lambda_lam / Re
        elif Re > self.Re_tur:
            term1 = (6.9 / Re) + (self.r / (3.7 * self.D_h)) ** 1.11
            return 1.0 / (-1.8 * log10(term1)) ** 2
        else:
            # Linear interpolation in transition region (simplified)
            f_lam = self.lambda_lam / self.Re_lam
            f_tur = 1.0 / (-1.8 * log10((6.9 / self.Re_tur) + (self.r / (3.7 * self.D_h)) ** 1.11)) ** 2
            return f_lam + (f_tur - f_lam) * (Re - self.Re_lam) / (self.Re_tur - self.Re_lam)

    def compute_pressure_loss(self, m_dot, mu, rho):
        """Сама функция расчёта потери давления"""
        Re = self.compute_reynolds(m_dot, mu, rho)
        f = self.compute_darcy_friction(Re)

        if Re < self.Re_lam:
            delta_p = (self.lambda_lam * mu * (self.L + self.L_eq) / 2) * (m_dot / (2 * rho * self.D_h ** 2 * self.S))
        else:
            delta_p = (f * (self.L + self.L_eq) / 2) * (m_dot * abs(m_dot) / (2 * rho * self.D_h * self.S ** 2))

        return delta_p

    def compute_output_pressure(self, p_in, m_dot_A, m_dot_B, mu, rho, temperature):
        self.p_in = p_in
        """Рассчитываем потери давления в обоих половинах трубы"""
        delta_p_A = self.compute_pressure_loss(m_dot_A, mu, rho)
        delta_p_B = self.compute_pressure_loss(m_dot_B, mu, rho)

        self.p_out = self.p_in - (delta_p_A + delta_p_B)/1e6
        self.T = temperature


# Пример использования:
if __name__ == "__main__":
    pipe = PipeModel()

    # Параметры от насоса
    p_in = 1e5  # Входное давление [Pa]
    m_dot_A = 0.5  # Параметр который надо рассчитывать в полной системе каким-то не очень понятным способом, поэтому я взял фикс. значения
    m_dot_B = 0.5  # Параметр который надо рассчитывать в полной системе каким-то не очень понятным способом, поэтому я взял фикс. значения
    mu = 1e-3  # Динамическая вязкость
    rho = 1000  # Плотность

    # Рассчитываем выходное давление
    pipe.compute_output_pressure(p_in, m_dot_A, m_dot_B, mu, rho)
    print(f"Выходное давление на сепаратор: {pipe.p_out:.2f} Па")
