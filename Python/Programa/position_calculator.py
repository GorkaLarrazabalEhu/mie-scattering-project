def sphere_positions(n, r, s):
    """
    Calculate the positions of the centers of n spheres
    with radius r and separation s between their edges.
    """
    if n <= 0:
        return []

    d = 2 * r + s  # distance between sphere centers
    positions = []

    if n % 2 == 1:
        # odd number of spheres → one at the origin
        positions.append(0)
        for i in range(1, (n // 2) + 1):
            positions.append(i * d)
            positions.append(-i * d)
    else:
        # even number of spheres → symmetric around origin
        offset = d / 2
        for i in range(n // 2):
            positions.append(-(offset + i * d))
            positions.append(offset + i * d)

    positions.sort()
    return positions


# --- Main program ---
if __name__ == "__main__":
    while True:    
        n = int(input("Enter number of spheres: "))
        r = float(input("Enter radius of each sphere: "))
        s = float(input("Enter separation between spheres (edge-to-edge): "))

        result = sphere_positions(n, r, s)
        print("Sphere positions:", result)
