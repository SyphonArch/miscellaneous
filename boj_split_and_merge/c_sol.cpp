#include <iostream>
#define MOD 1'000'000'007
#define RANGE(var, n) for (var = 0; var < n; ++var)
#define ll long long
using namespace std;

ll power(ll x, ll y);
ll inverse(ll n);
ll divide(ll x, ll y);
ll combination(ll n, ll r);
ll combination_with_repetition(ll n, ll r);
ll entringer_number(ll n, ll k);
ll euler_number(ll n);
ll factorial(ll n);

ll entringer[3001][3001];

int a[3001];
int b[3001];

ll seg_sizes[3001];

int main() {
    // fast io
    ios::sync_with_stdio(false);
    cin.tie(nullptr);

    // input
    int l, n;
    cin >> l >> n;
    int i;
    int head = 0;
    int tmp;
    RANGE(i, n) {
        cin >> tmp;
        head += tmp;
        a[head] = 1;
    }
    int m;
    head = 0;
    cin >> m;
    RANGE(i, m) {
        cin >> tmp;
        head += tmp;
        b[head] = 1;
    }

    // processing
    int open = 0;
    int segments = 0;
    for (i = 1; i < l + 1; ++i) {
        if (a[i] == 1 && a[i] == b[i]) {
            seg_sizes[segments] = i - open;
            ++segments;
            open = i;
        }
    }
    
    ll operations = 0;
    ll answer = 1;
    int location = 0;
    
    for (i = 0; i < segments; ++i) {
        bool its_a_trap = seg_sizes[i] == 2 && a[location + 1] == 0 && b[location + 1] == 0;
        if (!its_a_trap) {

            operations += seg_sizes[i] - 1;
            answer *= euler_number(seg_sizes[i]);
            answer %= MOD;

            answer = divide(answer, factorial(seg_sizes[i] - 1));  // LINE 0: divide by segment operations

        }
        location += seg_sizes[i];
    }
    answer *= factorial(operations); // LINE 1: multiply by total operations
    // [LINE 0] and [LINE 1] together calculate the number of ways in which segment operations can be
    // ordered, when all put together.
    answer %= MOD;

    cout << operations << " " << answer << endl;
} 

ll power(ll x, ll y) {
    ll result = 1;
    ll product = x;
    while (y != 0) {
        int lsb = y & 1;
        if (lsb) {
            result *= product;
            result %= MOD;
        }
        y = y >> 1;
        product *= product;
        product %= MOD;
    }
    return result;
}

ll inverse(ll n) {
    return power(n, MOD - 2);
}

ll divide(ll x, ll y) {
    return (x * inverse(y)) % MOD;
}

ll combination(ll n, ll r) {
    ll rslt = 1;
    for (ll i = n; i > r; --i) {
        rslt *= i;
        rslt %= MOD;
    }
    for (ll i = n - r; i > 1; --i) {
        rslt = divide(rslt, i);
    }
    return rslt;
}

ll combination_with_repetition(ll n, ll r) {
    return combination(n + r - 1, r);
}

ll entringer_number(ll n, ll k) {
    if (entringer[n][k]) {
        return entringer[n][k];
    } else {
        ll rslt;
        if (n == 1 && k == 1){
            rslt = 1;
        } else if (k >= n || k < 1) {
            return 0;
        } else {
            rslt = entringer_number(n, k - 1) + entringer_number(n - 1, n - k);
            rslt %= MOD;
        }
        entringer[n][k] = rslt;
        return rslt;
    }
}

ll euler_number(ll n) {
    ll rslt = 0;
    if (n <= 2) {
        rslt = 1;
    } else {
        for (ll i = 1; i <= n; ++i) {
            rslt += entringer_number(n, i);
            rslt %= MOD;
        }
    }
    return rslt;
}

ll factorial(ll n) {
    ll rslt = 1;
    for (ll i = n; i > 1; --i) {
        rslt *= i;
        rslt %= MOD;
    }
    return rslt;
}

