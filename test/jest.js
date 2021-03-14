const user = {
    createUser: () => {
        const userName = { firstName: "John"}
        userName['lastName'] = "Sangalang";
        return userName;
    }
};

//export it so it can be used 
module.exports = user;