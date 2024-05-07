const bcrypt = require('bcrypt')
const saltRounds = 10

/**
 *
 * @param { String } password
 * @returns { String }
 */
const encode = async (password) => await bcrypt.hash(password, saltRounds)
/**
 *
 * @param { String } password
 * @param { String } passwordInDB
 * @returns { Boolean }
 */

const checkPassword = async (password, passwordInDB) =>
    await bcrypt.compare(password, passwordInDB)
module.exports = {
    encode,
    checkPassword,
}
