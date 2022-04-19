/**
 * This script is used as the main Arduino script.
 * Currently this script only controls the charging rails.
 *
 * @author Billie Strong
 */

// This macro is required since cctl automagically checks for version
// mismatches. If this is not provided, then the script cannot work and cannot
// be compiled. You can use the -D flag as: -DVERSION=0.5.0 if you are manually
// compiling. Note that cctl.daughters.arduino does this automatically for you.
#ifndef VERSION
#error "You must provide the version in order to compile the Arduino "
       "daughterboard program."
#endif

#define BAUD_RATE 115200
#define RELAY_PINS {A1, A3, A5}  // The pins hooked up to the relay.
#define COMMAND_POLL_DELAY 100  // The polling delay used if no command is
                                // sent.

/**
 * The ChargeRelays namespace contains functions which control the relays used
 * in the charging rails.
 */
namespace ChargeRelays {
    const int pins[] = RELAY_PINS;
    const size_t pinCount = sizeof(pins) / sizeof(pins[0]);

    /**
     * Initializes the relevant pins as output.
     */
    void init() {
        for (size_t i = 0; i < pinCount; ++i) {
            pinMode(pins[i], OUTPUT);
        }
    }

    /**
     * Turns on the charging relays on or off.
     *
     * @param state Whether the relays should be on or off.
     */
    void setState(bool state) {
        for (size_t i = 0; i < pinCount; ++i) {
            digitalWrite(pins[i], state);
        }
    }
}

/**
 * Communication-related functions.
 */
namespace {
    /**
     * Initializes serial communication.
     */
    void init() {
        Serial.begin(BAUD_RATE);
    }

    /**
     * Reports the version to cctl.
     */
    void reportVersion() {
        Serial.println(VERSION);
    }
}

/**
 * Initializes pins as output and closes the relays so the charging may
 * proceed.
 */
void setup() {
    ChargeRelays::init();
    Comm::init();

    ChargeRelays::setState(HIGH);
}

/**
 * Sleeps until a Serial command is issued. If the command issued is
 * 'A', then it turns on the charging relays. If the command is 'D', then it
 * depresses the relays. If the command is 'V', then the program will report
 * its version back to cctl. All other commands are ignored.
 */
void loop() {
    // Sleep if no command is issued.
    while (Serial.available() == 0) { delay(COMMAND_POLL_DELAY); }

    // Otherwise, handle the command.
    switch (Serial.read()) {
        case 'A':
            ChargeRelays::setState(HIGH);
            break;
        case 'D':
            ChargeRelays::setState(LOW);
            break;
        case 'V':
            Comm::reportVersion();
            break;
    }
}
