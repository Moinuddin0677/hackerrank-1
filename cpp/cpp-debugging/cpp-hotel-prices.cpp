// C++ > Debugging > Hotel Prices
// Debug the existing class definitions so the total hotel's profit is calculated correctly.
//
// https://www.hackerrank.com/challenges/cpp-hotel-prices/problem
//

#include <iostream>
#include <vector>

using namespace std;

class HotelRoom {
public:
    HotelRoom(int bedrooms, int bathrooms)
    : bedrooms_(bedrooms), bathrooms_(bathrooms) {}

    virtual ~HotelRoom()
    {}

    virtual int get_price() {
        return 50*bedrooms_ + 100*bathrooms_;
    }
private:
    int bedrooms_;
    int bathrooms_;
};

class HotelApartment : public HotelRoom {
public:
    HotelApartment(int bedrooms, int bathrooms)
    : HotelRoom(bedrooms, bathrooms) {}

    virtual ~HotelApartment()
    {}

    virtual int get_price() override {
        return HotelRoom::get_price() + 100;
    }
};

int main() {
    int n;
    cin >> n;
    vector<HotelRoom*> rooms;
    for (int i = 0; i < n; ++i) {
        string room_type;
        int bedrooms;
        int bathrooms;
        cin >> room_type >> bedrooms >> bathrooms;
        if (room_type == "standard") {
            rooms.push_back(new HotelRoom(bedrooms, bathrooms));
        } else {
            rooms.push_back(new HotelApartment(bedrooms, bathrooms));
        }
    }

    int total_profit = 0;
    for (auto room : rooms) {
        total_profit += room->get_price();
    }
    cout << total_profit << endl;

    for (auto room : rooms) {
        delete room;
    }
    rooms.clear();

    return 0;
}