#pragma once

// Unico lugar del codigo que sabe de OpenMP. Si el build no lo detecto
// (_OPENMP no definido), cae a un for serial: el resto del codigo no
// necesita saber cual de los dos casos esta corriendo.
template <class F>
void parallelFor(int n, F&& body) {
#ifdef _OPENMP
#pragma omp parallel for schedule(dynamic)
#endif
    for (int i = 0; i < n; ++i) {
        body(i);
    }
}
